import os
import time
import logging
import sqlite3
import shutil
import glob
import requests
import schedule
from datetime import datetime, timedelta
from config import config

logger = logging.getLogger("bot")

__version__ = "1.0.0"

DB_PATH = "/app/data/sync.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS pending_removals
                 (user_id text, space_id text, detected_at timestamp, PRIMARY KEY (user_id, space_id))''')
    conn.commit()
    conn.close()

def backup_db():
    if not os.path.exists(DB_PATH):
        return

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    backup_path = f"{DB_PATH}.{timestamp}.bak"
    try:
        shutil.copy2(DB_PATH, backup_path)
        logger.info(f"Database backed up to {backup_path}")
        
        # Retention Policy
        backups = glob.glob(f"{DB_PATH}.*.bak")
        backups.sort(key=os.path.getmtime) # Oldest first
        
        retention = config.db_backup_retention_count
        if len(backups) > retention:
            to_delete = backups[:-retention]
            for f in to_delete:
                os.remove(f)
                logger.info(f"Deleted old backup: {f}")
                
    except Exception as e:
        logger.error(f"Backup failed: {e}")

def get_authentik_group_members(group_name):
    # This requires looking up group ID first or using a filter
    # Assuming group_name is unique
    headers = {"Authorization": f"Bearer {config.authentik_token}"}
    
    # 1. Find Group ID
    url = f"{config.authentik_url}/api/v3/core/groups/?name={group_name}"
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    data = resp.json()
    if not data['results']:
        logger.error(f"Authentik Group not found: {group_name}")
        return []
    
    group_pk = data['results'][0]['pk']
    
    # 2. Get Members
    # Authentik doesn't have a direct "get members of group" endpoint in v3 core/groups usually,
    # it's often user-centric or requires filtering users by group.
    # We can filter users by group__name
    url = f"{config.authentik_url}/api/v3/core/users/?groups__name={group_name}"
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    users = resp.json()['results']
    
    # Extract Matrix IDs
    # Assuming Matrix ID is stored in 'attributes' under 'matrix_id' OR we derive it from username
    # Let's assume username is the localpart for now or check attributes
    matrix_ids = []
    for u in users:
        # Check attributes first
        mid = u.get('attributes', {}).get('matrix_id')
        if not mid:
            # Fallback to username
            # This is a broad assumption, might need refinement based on user setup
            localpart = u['username']
            # Assuming homeserver domain from config isn't available easily here without parsing
            # So we rely on accurate mapping or attribute
            # We will use the configured matrix user's domain as a guess if not in attribute
            domain = config.matrix_user_id.split(':')[-1]
            mid = f"@{localpart}:{domain}"
        matrix_ids.append(mid)
        
    return matrix_ids

def get_matrix_room_members(room_id):
    # Use Synapse Admin API if possible for complete list, or CS API joined_members
    # CS API: GET /_matrix/client/v3/rooms/{roomId}/joined_members
    url = f"{config.matrix_homeserver}/_matrix/client/v3/rooms/{room_id}/joined_members"
    headers = {"Authorization": f"Bearer {config.matrix_access_token}"}
    resp = requests.get(url, headers=headers)
    
    if resp.status_code == 403: # Not in room?
        logger.warning(f"Bot not in room {room_id}, cannot fetch members (or not admin). Attempting to join.")
        join_resp = requests.post(f"{config.matrix_homeserver}/_matrix/client/v3/join/{room_id}", headers=headers)
        if join_resp.status_code == 200:
             # Retry fetch
             resp = requests.get(url, headers=headers)
    
    if resp.status_code != 200:
        logger.error(f"Failed to get members for {room_id}: {resp.text}")
        return []
        
    data = resp.json()
    return list(data.get('joined', {}).keys())

def invite_user(room_id, user_id):
    url = f"{config.matrix_homeserver}/_matrix/client/v3/rooms/{room_id}/invite"
    headers = {"Authorization": f"Bearer {config.matrix_access_token}"}
    data = {"user_id": user_id}
    resp = requests.post(url, headers=headers, json=data)
    if resp.status_code == 200:
        logger.info(f"Invited {user_id} to {room_id}")
    elif "is already in the room" in resp.text:
        pass # Ignore
    else:
        logger.error(f"Failed to invite {user_id}: {resp.text}")

def force_join_user(room_id, user_id):
    # /_synapse/admin/v1/join/<room_idOrAlias>
    url = f"{config.matrix_homeserver}/_synapse/admin/v1/join/{room_id}"
    headers = {"Authorization": f"Bearer {config.matrix_access_token}"}
    data = {"user_id": user_id}
    resp = requests.post(url, headers=headers, json=data)
    if resp.status_code == 200:
        logger.info(f"Force joined {user_id} to {room_id}")
    else:
        logger.error(f"Failed to force join {user_id}: {resp.text}")

def kick_user(room_id, user_id):
    url = f"{config.matrix_homeserver}/_matrix/client/v3/rooms/{room_id}/kick"
    headers = {"Authorization": f"Bearer {config.matrix_access_token}"}
    data = {"user_id": user_id, "reason": "Account sync cleanup"}
    resp = requests.post(url, headers=headers, json=data)
    if resp.status_code == 200:
        logger.info(f"Kicked {user_id} from {room_id}")
    else:
        logger.error(f"Failed to kick {user_id}: {resp.text}")

def sync_job():
    logger.info("Starting sync job...")
    
    # Pre-sync backup logic? Maybe only if we detect changes? 
    # Current plan says: Backup before destructive actions.
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    for mapping in config.mappings:
        group = mapping.get('group')
        space = mapping.get('space')
        method = mapping.get('method', config.join_method) # Local override or global
        
        if not group or not space:
            continue
            
        logger.info(f"Syncing Group '{group}' to Space '{space}'")
        
        auth_members = set(get_authentik_group_members(group))
        matrix_members = set(get_matrix_room_members(space))
        
        # ADD USERS
        to_add = auth_members - matrix_members
        for user_id in to_add:
            if user_id == config.matrix_user_id: continue
            
            logger.info(f"User {user_id} missing in {space}. Action: {method}")
            
            # Remove from pending removal if exists
            c.execute("DELETE FROM pending_removals WHERE user_id=? AND space_id=?", (user_id, space))
            conn.commit()
            
            if method == 'force':
                force_join_user(space, user_id)
            else:
                invite_user(space, user_id)
                
        # REMOVE USERS
        to_remove = matrix_members - auth_members
        for user_id in to_remove:
            if user_id == config.matrix_user_id: continue # Don't kick self
            
            # Check DB
            c.execute("SELECT detected_at FROM pending_removals WHERE user_id=? AND space_id=?", (user_id, space))
            row = c.fetchone()
            
            if not row:
                # First detection
                logger.info(f"User {user_id} not in group '{group}' but in space '{space}'. Starting grace period.")
                c.execute("INSERT INTO pending_removals (user_id, space_id, detected_at) VALUES (?, ?, ?)", 
                          (user_id, space, datetime.now()))
                conn.commit()
            else:
                detected_at = datetime.fromisoformat(row[0])
                if datetime.now() - detected_at > timedelta(minutes=config.cleanup_grace_period_minutes):
                    logger.info(f"Grace period expired for {user_id} in {space}. Removing...")
                    
                    # BACKUP BEFORE DESTRUCTION
                    backup_db()
                    
                    if config.remove_action == 'kick':
                        kick_user(space, user_id)
                    elif config.remove_action == 'ban':
                        # implement ban if needed, currently reusing kick
                        kick_user(space, user_id) # Placeholder
                        
                    # Remove from DB
                    c.execute("DELETE FROM pending_removals WHERE user_id=? AND space_id=?", (user_id, space))
                    conn.commit()
                else:
                    logger.debug(f"User {user_id} pending removal. Grace period remaining.")

    conn.close()
    logger.info("Sync job finished.")

def run():
    if not config.validate():
        sys.exit(1)
    
    logger.info(f"Starting Authentik-Matrix Sync Bot v{__version__}")
    init_db()
    
    # Run once immediately
    sync_job()
    
    # Schedule
    schedule.every(config.sync_interval).seconds.do(sync_job)
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    run()
