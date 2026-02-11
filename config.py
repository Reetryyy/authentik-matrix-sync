import os
import sys
import logging
import json

# Configure logging
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = os.environ.get("LOG_FORMAT", "text")

handler = logging.StreamHandler(sys.stdout)
if LOG_FORMAT == "json":
    # Basic JSON formatter could be added here if needed, keeping simple for now
    formatter = logging.Formatter('{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}')
else:
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

handler.setFormatter(formatter)
logging.basicConfig(level=LOG_LEVEL, handlers=[handler])
logger = logging.getLogger("config")

class Config:
    def __init__(self):
        # Authentik
        self.authentik_url = os.environ.get("AUTHENTIK_URL")
        self.authentik_token = os.environ.get("AUTHENTIK_TOKEN")

        # Matrix
        self.matrix_homeserver = os.environ.get("MATRIX_HOMESERVER_URL")
        self.matrix_user_id = os.environ.get("MATRIX_USER_ID")
        self.matrix_access_token = os.environ.get("MATRIX_ACCESS_TOKEN")

        # Sync Logic
        self.sync_interval = int(os.environ.get("SYNC_INTERVAL_SECONDS", 60))
        self.join_method = os.environ.get("JOIN_METHOD", "invite").lower() # invite or force
        
        # Mappings
        # Expecting JSON string: [{"group": "A", "space": "!abc:matrix.org"}, ...]
        mappings_str = os.environ.get("SYNC_MAPPINGS", "[]")
        try:
            self.mappings = json.loads(mappings_str)
        except json.JSONDecodeError:
            logger.error("Failed to parse SYNC_MAPPINGS JSON. Ensure it is valid JSON.")
            self.mappings = []

        # Lifecycle
        self.cleanup_grace_period_minutes = int(os.environ.get("CLEANUP_GRACE_PERIOD_MINUTES", 120)) # 2 hours
        self.remove_action = os.environ.get("REMOVE_ACTION", "kick").lower() # kick, ban, none
        
        # Backup
        self.db_backup_retention_count = int(os.environ.get("DB_BACKUP_RETENTION_COUNT", 3))

    def validate(self):
        errors = []
        if not self.authentik_url: errors.append("AUTHENTIK_URL is missing")
        if not self.authentik_token: errors.append("AUTHENTIK_TOKEN is missing")
        if not self.matrix_homeserver: errors.append("MATRIX_HOMESERVER_URL is missing")
        if not self.matrix_user_id: errors.append("MATRIX_USER_ID is missing")
        if not self.matrix_access_token: errors.append("MATRIX_ACCESS_TOKEN is missing")
        
        if self.join_method not in ["invite", "force"]:
             errors.append(f"Invalid JOIN_METHOD: {self.join_method}. Must be 'invite' or 'force'")

        if errors:
            for err in errors:
                logger.error(err)
            return False
        return True

config = Config()
