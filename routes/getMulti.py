from typing import Any, Dict, Optional

import aiohttp
from config import HEADERS


async def get_account_multiplier(account_id: str) -> Optional[Dict[str, Any]]:
    """
    Get the multiplier (notional) value for an account from its settings
    """
    url = "https://www.trade-copier.com/webservice/v4/settings/getSettings.php"

    # Filter by slave ID (which is the same as account_id)
    filter_data = {'id_slave': account_id}

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=HEADERS, data=filter_data, timeout=20) as response:
                response.raise_for_status()
                data = await response.json()

                # API returns {"settings": [...]} structure
                if isinstance(data, dict) and "settings" in data and data["settings"]:
                    # Find the setting with risk_factor_type = 3 (Multiplier - Notional)
                    for setting in data["settings"]:
                        if setting.get("risk_factor_type") == 11:
                            return {
                                "account_id": account_id,
                                "slave_name": setting.get("slave_name", "Unknown"),
                                "master_name": setting.get("master_name", "Unknown"),
                                "multiplier_value": setting.get("risk_factor_value", 0.0),
                                "risk_factor_type": setting.get("risk_factor_type", 0),
                                "risk_factor_type_string": setting.get("risk_factor_type_string", "Unknown"),
                                "copier_status": setting.get("copier_status", 0),
                                "copier_status_string": setting.get("copier_status_string", "Unknown")
                            }

                    # If no multiplier setting found, return first setting with details
                    if data["settings"]:
                        first_setting = data["settings"][0]
                        return {
                            "account_id": account_id,
                            "slave_name": first_setting.get("slave_name", "Unknown"),
                            "master_name": first_setting.get("master_name", "Unknown"),
                            "multiplier_value": None,  # No multiplier set
                            "risk_factor_type": first_setting.get("risk_factor_type", 0),
                            "risk_factor_type_string": first_setting.get("risk_factor_type_string", "Unknown"),
                            "copier_status": first_setting.get("copier_status", 0),
                            "copier_status_string": first_setting.get("copier_status_string", "Unknown")
                        }

                return None

        except Exception as e:
            print(f"Error fetching multiplier for account {account_id}: {e}")
            return None

async def get_formatted_multiplier_info(account_id: str) -> str:
    """
    Get formatted multiplier information string
    """
    multiplier_data = await get_account_multiplier(account_id)

    if not multiplier_data:
        return f"Could not retrieve multiplier settings for account {account_id}"

    if multiplier_data["multiplier_value"] is not None:
        return (
            f"Multiplier Settings\n"
            f"Account: {multiplier_data['slave_name']}\n"
            f"Master: {multiplier_data['master_name']}\n"
            f"Multiplier Value: {multiplier_data['multiplier_value']}\n"
            f"Risk Type: {multiplier_data['risk_factor_type_string']}\n"
            f"Status: {multiplier_data['copier_status_string']}"
        )
    else:
        return (
            f"No Multiplier Set\n"
            f"Account: {multiplier_data['slave_name']}\n"
            f"Master: {multiplier_data['master_name']}\n"
            f"Current Risk Type: {multiplier_data['risk_factor_type_string']}\n"
            f"Status: {multiplier_data['copier_status_string']}"
        )

# Usage examples:
# multiplier_data = await get_account_multiplier("biGOJaKtb")
# formatted_info = await get_formatted_multiplier_info("biGOJaKtb")
