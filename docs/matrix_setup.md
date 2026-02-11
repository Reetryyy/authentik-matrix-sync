# Matrix Access Token Guide

The bot requires an Access Token to interact with your Matrix Homeserver.

## 1. Create the Bot Account
### Option A: Manual Registration
Register a new account on your homeserver if you have registration enabled.
- **Username**: `bot` (or `authentik-bot`)
- **Password**: `<secure-password>`

### Option B: Via Authentik (SSO)
If you rely on Authentik for user management:
1.  Create a "User" in Authentik for the bot (e.g. `bot`).
2.  **Log in** with this user via Element (or any Matrix client) once.
    - This is required to initialize the user in the Synapse database.
3.  The username will likely be `@bot:yourdomain.com`.

## 2. Make the Bot an Admin (Required for 'Force Join')
If you use `JOIN_METHOD=force`, the bot **MUST** be a server admin to invite/join users automatically.

### Option A: Using Synapse Admin UI (Easiest)
**Prerequisite**: You already have another Admin account.
1.  Log in with your existing Admin account.
2.  Go to **Users**.
3.  Find `@bot:yourdomain.com`.
4.  Check **Admin**.

### Option B: Using SQL (If you have NO admins yet)
If this is your first Admin user (or your SSO user needs to be promoted manually):

1. Access your Postgres database container:
```bash
docker exec -it synapse-postgres psql -U synapse_user synapse
```
2. Run this SQL command (replace `@bot:yourdomain.com` with the actual Matrix ID):
```sql
UPDATE users SET admin = 1 WHERE name = '@bot:yourdomain.com';
```
3. Type `\q` to exit.

## 3. Get the Access Token
### Method 1: Using Curl (Preferred / Non-SSO)
If you have a password (Option A), you can generate a token directly via the login API:

```bash
curl -X POST \
     -d '{"type":"m.login.password", "user":"bot", "password":"<BOT_PASSWORD>"}' \
     "https://<MATRIX_HOMESERVER_URL>/_matrix/client/r0/login"
```

**Response:**
```json
{
  "user_id": "@bot:yourdomain.com",
  "access_token": "syt_AiGs...",
  ...
}
```

### Method 2: Element Web (Preferred for SSO)
If you use SSO (Option B), you must get the token from an existing session.

1.  Log in to Element Web with the bot account (via SSO).
2.  Click on your **Profile Picture** -> **All Settings**.
3.  Go to **Help & About**.
4.  Scroll to the bottom and click **Advanced**.
5.  Find **Access Token** and click to reveal it.
6.  Copy the token.

> [!WARNING]
> If you log out of this session in Element, the token will be invalidated. Do NOT log out; instead, use an Incognito window or a different browser profile to get the token, then close the window.
