import os
import sys
import requests
from config import config

def check_authentik():
    url = f"{config.authentik_url}/api/v3/core/users/me/"
    headers = {"Authorization": f"Bearer {config.authentik_token}"}
    try:
        resp = requests.get(url, headers=headers, timeout=5)
        resp.raise_for_status()
        return True
    except Exception as e:
        print(f"Authentik Check Failed: {e}", file=sys.stderr)
        return False

def check_matrix():
    # Use versions endpoint as a lightweight check
    url = f"{config.matrix_homeserver}/_matrix/client/versions"
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        return True
    except Exception as e:
        print(f"Matrix Check Failed: {e}", file=sys.stderr)
        return False

if __name__ == "__main__":
    if not config.validate():
        print("Configuration Invalid", file=sys.stderr)
        sys.exit(1)

    auth_ok = check_authentik()
    matrix_ok = check_matrix()

    if auth_ok and matrix_ok:
        print("Healthy")
        sys.exit(0)
    else:
        sys.exit(1)
