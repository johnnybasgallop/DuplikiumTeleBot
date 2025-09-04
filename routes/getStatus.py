from typing import Any, Dict, Optional

import aiohttp
from config import GET_ACCOUNTS, HEADERS


async def check_account_details(account_id: str) -> Optional[Dict[str, Any]]:
    """
    Get account details by filtering the getAccounts endpoint
    """
    async with aiohttp.ClientSession() as session:
        try:
            # Use the existing getAccounts endpoint with filter
            filter_data = {'account_id': account_id}

            async with session.post(GET_ACCOUNTS, headers=HEADERS, data=filter_data, timeout=20) as response:
                response.raise_for_status()
                data = await response.json()

                # The API returns {"accounts": [...]} structure
                if isinstance(data, dict) and "accounts" in data and data["accounts"]:
                    account = data["accounts"][0]  # First (and only) account from filter

                    return {
                        "account_id": account_id,
                        "name": account.get("name", "Unknown"),
                        "equity": float(account.get("equity", 0)),
                        "balance": float(account.get("balance", 0)),
                        "free_margin": float(account.get("free_margin", 0)),
                        "status": account.get("status", 0),
                        "state": account.get("state", "UNKNOWN")
                    }

                return None

        except Exception as e:
            print(f"Error fetching account details for {account_id}: {e}")
            return None

async def get_account_info(account_id: str) -> str:
    """
    Get formatted account information string with green colored values
    """
    details = await check_account_details(account_id)

    if not details:
        return f"❌ Could not retrieve details for account {account_id}"

    status_emoji = "🟢" if details['status'] == 1 else "🔴"
    status_text = "Enabled" if details['status'] == 1 else "Disabled"

    # Connection state emoji
    state_emojis = {
        "CONNECTED": "🟢",
        "DISCONNECTED": "🔴",
        "SYMBOL_NOT_FOUND": "⚠️",
        "ORDER_FAILED": "❌",
        "INVESTOR_PASSWORD": "🔐",
        "NONE": "⚫"
    }
    state_emoji = state_emojis.get(details['state'], "❓")

    return (
        f"📊 <b>Account Details</b>\n\n"
        f"🆔 <b>Account ID:</b> <span class='tg-spoiler'>{details['account_id']}</span>\n"
        f"📝 <b>Name:</b> {details['name']}\n\n"
        f"💰 <b>Balance:</b> <code>${details['balance']:,.2f}</code>\n"
        f"📈 <b>Equity:</b> <code>${details['equity']:,.2f}</code>\n"
        f"💳 <b>Free Margin:</b> <code>${details['free_margin']:,.2f}</code>\n\n"
        f"{status_emoji} <b>Status:</b> {status_text}\n"
        f"{state_emoji} <b>Connection:</b> {details['state']}"
    )
