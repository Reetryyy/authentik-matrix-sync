# Authentik to Matrix Group Sync Bot

A Dockerized Python bot that synchronizes user membership from [Authentik](https://goauthentik.io/) groups to [Matrix](https://matrix.org/) Spaces/Rooms.

## Features

- **Group Sync**: Automatically adds users from an Authentik Group to a Matrix Space/Room.
- **Configurable Join**: Supports standard **Invites** or **Force Join** (via Synapse Admin API).
- **Lifecycle Management**:
    - Detects when a user is removed from an Authentik Group.
    - Configurable **Grace Period** (default 24h) before removing the user from Matrix.
    - Supports **Kick** or **Ban** actions.
- **Safety & Resilience**:
    - **State Persistence**: Uses a local SQLite database to track grace periods.
    - **Auto-Backups**: Automatically backs up the state database before any destructive action (kick/ban).
    - **Retention Policy**: Automatically rotates old backups to save space.
- **Health Monitoring**: Built-in healthcheck script and endpoint.

## Configuration

The bot is configured entirely via Environment Variables.

| Variable | Description | Default |
| :--- | :--- | :--- |
| `AUTHENTIK_URL` | Base URL of your Authentik instance (e.g., `https://auth.example.com`) | Required |
| `AUTHENTIK_TOKEN` | Authentik API Token | Required |
| `MATRIX_HOMESERVER_URL` | Base URL of your Matrix Homeserver (e.g., `https://matrix.example.com`) | Required |
| `MATRIX_USER_ID` | The user ID of the bot (e.g., `@bot:example.com`) | Required |
| `MATRIX_ACCESS_TOKEN` | Access token for the bot user | Required |
| `SYNC_MAPPINGS` | JSON string defining the sync logic (see below) | `[]` |
| `JOIN_METHOD` | How to add users: `invite` or `force` (requires Admin) | `invite` |
| `SYNC_INTERVAL_SECONDS` | How often to run the sync job | `60` |
| `CLEANUP_GRACE_PERIOD_MINUTES` | Time to wait before removing a user after they leave the group | `120` |
| `REMOVE_ACTION` | Action to take on removal: `kick` or `ban` | `kick` |
| `DB_BACKUP_RETENTION_COUNT` | Number of database backups to keep | `3` |
| `LOG_LEVEL` | Logging verbosity: `DEBUG`, `INFO`, `WARNING`, `ERROR` | `INFO` |

### Mapping Configuration (`SYNC_MAPPINGS`)

This variable expects a JSON string array of objects:

```json
[
  {
    "group": "Authentik Group Name",
    "space": "!matrixRoomOrSpaceId:example.com",
    "method": "force" 
  }
]
```
*Note: `method` in the mapping is optional and overrides the global `JOIN_METHOD`.*

## Deployment (Docker Compose)

Add the following service to your `docker-compose.yml`:

```yaml
services:
  authentik-matrix-sync:
    build: ./Bots/oidc_sync
    container_name: authentik-matrix-sync
    restart: unless-stopped
    security_opt:
      - no-new-privileges:true
    read_only: true
    cap_drop:
      - ALL
    user: "1000:1000"
    volumes:
      - bot_data:/app/data
    environment:
      - AUTHENTIK_URL=https://auth.example.com
      - AUTHENTIK_TOKEN=your_token
      - MATRIX_HOMESERVER_URL=https://matrix.example.com
      - MATRIX_USER_ID=@bot:example.com
      - MATRIX_ACCESS_TOKEN=your_matrix_token
      - JOIN_METHOD=force
      - SYNC_MAPPINGS=[{"group":"Admins","space":"!admins:example.com"}]

volumes:
  bot_data:
```

## Contributors

- **kaxak** - Initial Idea & Requirements
- **Antigravity** (Google DeepMind) - Implementation

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
