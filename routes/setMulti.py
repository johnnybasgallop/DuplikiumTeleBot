from typing import Any, Dict, Optional

import aiohttp
from config import HEADERS


async def set_account_multiplier(account_id: str, multiplier_value: float) -> Optional[Dict[str, Any]]:
    """
    Set the multiplier (lot) value for an account using setSettings API
    Always uses the known master_id to update existing settings
    """
    url = "https://www.trade-copier.com/webservice/v4/settings/setSettings.php"

    # Your master_id
    MASTER_ID = "dXiOJaKtb"

    # Create settings object with master_id to ensure we update existing setting
    setting = {
        'id_slave': account_id,
        'id_master': MASTER_ID,  # Always include master_id
        'risk_factor_type': 11,  # 11 = Multiplier (Lot)
        'risk_factor_value': float(multiplier_value)
    }

    # API expects an array of settings
    settings_array = [setting]

    print(f"Setting multiplier (lot) for slave {account_id} with master {MASTER_ID}: {multiplier_value}")
    print(f"Sending data: {settings_array}")

    async with aiohttp.ClientSession() as session:
        try:
            # Use form data with array structure
            form_data = {}
            for i, setting_item in enumerate(settings_array):
                for key, value in setting_item.items():
                    form_data[f'{i}[{key}]'] = str(value)

            print(f"Form data: {form_data}")

            async with session.post(url, headers=HEADERS, data=form_data, timeout=20) as response:
                print(f"Response status: {response.status}")

                if response.status == 200:
                    data = await response.json()
                    print(f"Success response: {data}")
                    return data
                else:
                    error_text = await response.text()
                    print(f"Error response ({response.status}): {error_text[:500]}...")
                    return None

        except aiohttp.ClientError as e:
            print(f"HTTP error setting multiplier for account {account_id}: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error setting multiplier for account {account_id}: {e}")
            return None

async def update_multiplier_with_confirmation(account_id: str, multiplier_value: float) -> str:
    """
    Update multiplier and return formatted confirmation message
    """
    result = await set_account_multiplier(account_id, multiplier_value)

    if result:
        return (
            f"<b>Multiplier Updated Successfully</b>\n\n"
            f"<b>Account ID:</b> <code>{account_id}</code>\n"
            f"<b>New Multiplier:</b> {multiplier_value}\n"
            f"<b>Risk Factor Type:</b> Multiplier (Lot)"
        )
    else:
        return f"❌ Failed to update multiplier for account {account_id}"
