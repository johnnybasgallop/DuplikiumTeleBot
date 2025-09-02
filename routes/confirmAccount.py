from typing import Any, Dict, List, Optional

import aiohttp
from config import GET_ACCOUNTS, HEADERS


async def fetch_accounts() -> List[Dict[str, Any]]:
    """Fetch accounts using async HTTP client"""
    async with aiohttp.ClientSession() as session:
        async with session.get(GET_ACCOUNTS, headers=HEADERS, timeout=20) as response:
            response.raise_for_status()
            data = await response.json()

    if isinstance(data, dict) and "accounts" in data:
        return data["accounts"]
    if isinstance(data, list):
        return data
    return []

async def find_account(login: str, password: str, require_slave: bool = True) -> Optional[Dict[str, Any]]:
    """
    Returns the matching account dict if (login, password) pair exists.
    If require_slave=True, only matches type==1 (slave) accounts.
    """
    login = str(login).strip()
    password = str(password)

    accounts = await fetch_accounts()  # <-- Now awaited
    for acc in accounts:
        if require_slave and acc.get("type") != 1:
            continue
        if str(acc.get("login")) == login and str(acc.get("password")) == password:
            return acc
    return None

async def confirm_account(login: str, password: str) -> Optional[str]:
    """
    Returns account_id if confirmed, otherwise None.
    """
    acc = await find_account(login, password, require_slave=True)  # <-- Now awaited
    return acc.get("account_id") if acc else None
