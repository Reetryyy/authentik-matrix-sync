# Authentik Setup Guide

To allow the bot to sync groups and users, you need to create a Service Account in Authentik and assign it the necessary read-only permissions via a Role.

## Prerequisites
- Authentik Admin access.

## Step 1: Create a Role
It is best practice to use a Role for permissions management rather than assigning them directly to a user.

1.  Log in to your Authentik Admin Interface.
2.  Navigate to **Directory** > **Groups**. (Authentik uses Groups/Roles interchangeably for permissions).
    *Note: In newer Authentik versions, this might be under Directory > Groups, or specifically "Roles" depending on version.*
3.  Click **Create**.
4.  **Name**: `matrix-sync-bot-role` (or similar).
5.  **Is Superuser**: **Disable** this (keep unchecked).
6.  Click **Create**.
7.  Click on the newly created group/role name to open its details.
8.  Go to the **Permissions** tab.
9.  Click **Assign new permission**.
10. Search for and select the following **Global** permissions:
    - `authentik_core | group | Can view group`
    - `authentik_core | user | Can view user`
11. Click **Assign**.

## Step 2: Create a Service Account
1.  Navigate to **Directory** > **Users**.
2.  Click **Create Service Account**.
3.  **Username**: `matrix-sync-bot`.
4.  **Create**.

## Step 3: Assign Role to Service Account
1.  Click on the `matrix-sync-bot` user you just created.
2.  Go to the **Groups** tab.
3.  Click **Add to group**.
4.  Select the `matrix-sync-bot-role` you created in Step 1.
5.  Click **Add**.

## Step 4: Generate Token
1.  Navigate to **Directory** > **Tokens & App passwords**.
2.  Click **Create**.
3.  **Identifier**: `matrix-sync-token`.
4.  **User**: Select `matrix-sync-bot`.
5.  **Expiring**: Uncheck this (unless you plan to rotate tokens manually).
6.  Click **Create**.
7.  **Copy the Key**. This is the value for your `AUTHENTIK_TOKEN` environment variable.
