# Matrix Access Token Guide

The bot requires an Access Token to interact with your Matrix Homeserver.

## Prerequisites
- A Matrix account on your homeserver (e.g., `@bot:yourdomain.com`).
- If you use `JOIN_METHOD=force`, this account must be a **Server Admin**.

## Method 1: Using Curl (Recommended)
You can generate a token directly via the login API.

Run this command in your terminal (replace values):

```bash
curl -X POST \
     -d '{"type":"m.login.password", "user":"<BOT_USERNAME>", "password":"<BOT_PASSWORD>"}' \
     "https://<MATRIX_HOMESERVER_URL>/_matrix/client/r0/login"
```

**Response:**
```json
{
  "user_id": "@bot:yourdomain.com",
  "access_token": "syt_AiGs...",
  "home_server": "yourdomain.com",
  "device_id": "..."
}
```
Copy the `access_token` value and use it in your `docker-compose.yml`.

## Method 2: Element Web
1.  Log in to Element Web with the bot account.
2.  Click on your **Profile Picture** -> **All Settings**.
3.  Go to **Help & About**.
4.  Scroll to the bottom and click **Advanced**.
5.  Find **Access Token** and click to reveal it.
6.  Copy the token.

> [!WARNING]
> If you log out of this session in Element, the token will be invalidated. It is better to use Method 1 to generate a dedicated session/token.
