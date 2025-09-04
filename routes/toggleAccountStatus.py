from typing import Any, Dict, Optional

import aiohttp
from config import HEADERS


async def enable_account(account_id: str) -> Optional[Dict[str, Any]]:
    """
    Enable an account by setting status to 1
    """
    url = "https://www.trade-copier.com/webservice/v4/account/updateAccount.php"

    data = {
        'account_id': account_id,
        'status': 1
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=HEADERS, data=data, timeout=20) as response:
                response.raise_for_status()
                result = await response.json()

                # API returns {"account": {...}} on success
                if isinstance(result, dict) and "account" in result:
                    return result["account"]

                return None

        except Exception as e:
            print(f"Error enabling account {account_id}: {e}")
            return None

async def disable_account(account_id: str) -> Optional[Dict[str, Any]]:
    """
    Disable an account by setting status to 0
    """
    url = "https://www.trade-copier.com/webservice/v4/account/updateAccount.php"

    data = {
        'account_id': account_id,
        'status': 0
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=HEADERS, data=data, timeout=20) as response:
                response.raise_for_status()
                result = await response.json()

                # API returns {"account": {...}} on success
                if isinstance(result, dict) and "account" in result:
                    return result["account"]

                return None

        except Exception as e:
            print(f"Error disabling account {account_id}: {e}")
            return None

# Helper function to toggle account status
async def toggle_account_status(account_id: str, enable: bool) -> str:
    """
    Toggle account status and return formatted result message
    """
    if enable:
        result = await enable_account(account_id)
        action = "enabled"
    else:
        result = await disable_account(account_id)
        action = "disabled"

    if result:
        status_text = "Enabled" if result.get('status') == 1 else "Disabled"
        return (
            f"Account successfully {action}!\n\n"
            f"Account ID: {result.get('account_id', 'Unknown')}\n"
            f"Name: {result.get('name', 'Unknown')}\n"
            f"Status: {status_text}"
        )
    else:
        return f"Failed to {action.replace('d', '')} account {account_id}"
