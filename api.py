from typing import Any, Dict, List, Optional

import requests

AUTH_USERNAME = "AJSeducation"
AUTH_TOKEN    = "GM0NGY1ODg2YTFjN2Y0NGY4NzVlMzc"
GET_ACCOUNTS  = "https://www.trade-copier.com/webservice/v4/account/getAccounts.php"

HEADERS = {
    "Auth-Username": AUTH_USERNAME,
    "Auth-Token": AUTH_TOKEN,
    "Accept": "application/json",
}

def fetch_accounts() -> List[Dict[str, Any]]:
    r = requests.get(GET_ACCOUNTS, headers=HEADERS, timeout=20)
    r.raise_for_status()
    data = r.json()
    if isinstance(data, dict) and "accounts" in data:
        return data["accounts"]
    if isinstance(data, list):
        return data
    return []

def find_account(login: str, password: str, require_slave: bool = True) -> Optional[Dict[str, Any]]:
    """
    Returns the matching account dict if (login, password) pair exists.
    If require_slave=True, only matches type==1 (slave) accounts.
    """
    login = str(login).strip()
    password = str(password)

    for acc in fetch_accounts():
        if require_slave and acc.get("type") != 1:
            continue
        if str(acc.get("login")) == login and str(acc.get("password")) == password:
            return acc
    return None

def confirm_account(login: str, password: str) -> Optional[str]:
    """
    Returns account_id if confirmed, otherwise None.
    """
    acc = find_account(login, password, require_slave=True)
    return acc.get("account_id") if acc else None

# --- Example usage ---
user_login = "3413108"
user_password = "&XhbV2*m"

account_id = confirm_account(user_login, user_password)
if account_id:
    print(f"confirmed, account_id={account_id}")
else:
    print("not found")
