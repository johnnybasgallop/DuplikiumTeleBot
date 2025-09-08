import asyncio
import os
from datetime import datetime, time, timezone
from typing import Any, Dict, Optional

import aiohttp
from config import GET_ACCOUNTS, HEADERS, db
from telegram import Bot
from telegram.error import TelegramError

# Initialize bot for sending messages
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)

async def find_telegram_id_for_account(account_id: str) -> Optional[str]:
    """
    Find the telegram ID for a given account ID
    """
    try:
        all_rows = db.table('algo-accounts').select("*").execute()

        if not all_rows.data:
            return None

        for row in all_rows.data:
            telegram_id = row.get('telegramId')
            accounts = row.get('accounts', [])

            for account in accounts:
                if account.get('accountId') == account_id:
                    return telegram_id

        return None

    except Exception as e:
        print(f"Error finding telegram ID for account {account_id}: {e}")
        return None

async def send_multiplier_update_notification(telegram_id: str, account_id: str, account_name: str, old_multiplier: float, new_multiplier: float, equity: float):
    """
    Send notification to user about multiplier update
    """
    try:
        message = (
            f"🔔 <b>Auto Compounding Update</b>\n\n"
            f"📊 <b>Account:</b> {account_name}\n"
            f"💰 <b>Current Equity:</b> £{equity:,.2f}\n"
            f"📈 <b>Multiplier Updated:</b> {old_multiplier} → {new_multiplier}\n\n"
            f"Your account has reached a new equity tier and the multiplier has been automatically adjusted for compounding growth."
        )

        await bot.send_message(
            chat_id=telegram_id,
            text=message,
            parse_mode='HTML'
        )

        print(f"Notification sent to {telegram_id} for account {account_id}")

    except TelegramError as e:
        print(f"Failed to send notification to {telegram_id}: {e}")
    except Exception as e:
        print(f"Unexpected error sending notification to {telegram_id}: {e}")

async def check_auto_compounding_status():
    """
    Check all accounts' auto compounding status and return array of objects
    """
    try:
        # Get all rows from algo-accounts table
        all_rows = db.table('algo-accounts').select("*").execute()

        if not all_rows.data:
            print("No account rows found in database")
            return []

        compounding_status_array = []

        # Iterate through each user's row
        for row in all_rows.data:
            telegram_id = row.get('telegramId', 'unknown')
            accounts = row.get('accounts', [])

            # Check each account in the user's accounts array
            for account in accounts:
                account_id = account.get('accountId')
                compounding_state = account.get('auto_compounding', False)

                if account_id:
                    compounding_status_array.append({
                        'accountId': account_id,
                        'compounding': compounding_state
                    })

        print(f"Found {len(compounding_status_array)} accounts with compounding status")
        return compounding_status_array

    except Exception as e:
        print(f"Error checking auto compounding status: {e}")
        return []

async def get_account_balance_and_multiplier(account_id: str) -> Optional[Dict[str, Any]]:
    """
    Get account equity and current multiplier for a specific account
    """
    async with aiohttp.ClientSession() as session:
        try:
            # Get equity from accounts API
            filter_data = {'account_id': account_id}
            async with session.post(GET_ACCOUNTS, headers=HEADERS, data=filter_data, timeout=20) as response:
                response.raise_for_status()
                account_data = await response.json()

                if not (isinstance(account_data, dict) and "accounts" in account_data and account_data["accounts"]):
                    return None

                account = account_data["accounts"][0]
                equity = float(account.get("equity", 0))
                balance = float(account.get("balance", 0))

            # Get current multiplier from settings API
            settings_url = "https://www.trade-copier.com/webservice/v4/settings/getSettings.php"
            settings_filter = {'id_slave': account_id}

            async with session.post(settings_url, headers=HEADERS, data=settings_filter, timeout=20) as response:
                response.raise_for_status()
                settings_data = await response.json()

                current_multiplier = None
                if isinstance(settings_data, dict) and "settings" in settings_data:
                    for setting in settings_data["settings"]:
                        if setting.get("risk_factor_type") == 11:  # Multiplier (Lot)
                            current_multiplier = float(setting.get("risk_factor_value", 0))
                            break

                return {
                    "account_id": account_id,
                    "balance": balance,
                    "equity": equity,
                    "current_multiplier": current_multiplier,
                    "name": account.get("name", "Unknown")
                }

        except Exception as e:
            print(f"Error getting equity/multiplier for {account_id}: {e}")
            return None

def calculate_compounding_multiplier(equity: float) -> float:
    """
    Calculate multiplier based on £3500 equity tiers
    """
    if equity < 3500:
        return 0.0

    multiplier = int(equity // 3500)
    return float(multiplier)

async def set_account_multiplier_simple(account_id: str, multiplier_value: float) -> bool:
    """
    Simplified version of set multiplier for scheduler use
    """
    url = "https://www.trade-copier.com/webservice/v4/settings/setSettings.php"
    MASTER_ID = "dXiOJaKtb"

    async with aiohttp.ClientSession() as session:
        try:
            form_data = {
                '0[id_slave]': account_id,
                '0[id_master]': MASTER_ID,
                '0[risk_factor_type]': '11',
                '0[risk_factor_value]': str(multiplier_value)
            }

            async with session.post(url, headers=HEADERS, data=form_data, timeout=20) as response:
                return response.status == 200

        except Exception as e:
            print(f"Error setting multiplier for {account_id}: {e}")
            return False

async def process_auto_compounding_accounts():
    """
    Process auto compounding accounts with equity-based tiers and send notifications
    """
    try:
        compounding_array = await check_auto_compounding_status()
        auto_compounding_accounts = [acc for acc in compounding_array if acc['compounding']]

        print(f"Found {len(auto_compounding_accounts)} accounts with auto compounding enabled")

        results = []

        for account_info in auto_compounding_accounts:
            account_id = account_info['accountId']

            # Get current balance, equity and multiplier
            account_data = await get_account_balance_and_multiplier(account_id)

            if not account_data:
                print(f"Could not get data for account {account_id}")
                continue

            equity = account_data['equity']
            current_multiplier = account_data['current_multiplier']

            if current_multiplier is None:
                print(f"No multiplier found for account {account_id}")
                continue

            # Calculate what multiplier should be based on equity
            target_multiplier = calculate_compounding_multiplier(equity)

            result = {
                'account_id': account_id,
                'name': account_data['name'],
                'equity': equity,
                'equity_tier': int(equity // 3500),
                'current_multiplier': current_multiplier,
                'target_multiplier': target_multiplier,
                'updated': False
            }

            # Only update if target multiplier is different from current AND it's an increase
            if target_multiplier != current_multiplier and target_multiplier > current_multiplier:
                success = await set_account_multiplier_simple(account_id, target_multiplier)
                result['updated'] = success

                if success:
                    print(f"Updated {account_id}: equity £{equity:,.2f} (tier {int(equity // 3500)}) -> multiplier {current_multiplier} -> {target_multiplier}")

                    # Find telegram ID and send notification
                    telegram_id = await find_telegram_id_for_account(account_id)
                    if telegram_id:
                        await send_multiplier_update_notification(
                            telegram_id=telegram_id,
                            account_id=account_id,
                            account_name=account_data['name'],
                            old_multiplier=current_multiplier,
                            new_multiplier=target_multiplier,
                            equity=equity
                        )
                    else:
                        print(f"Could not find telegram ID for account {account_id}")
                else:
                    print(f"Failed to update {account_id} multiplier")
            elif target_multiplier < current_multiplier:
                # Handle multiplier decrease (equity dropped below tier)
                success = await set_account_multiplier_simple(account_id, target_multiplier)
                result['updated'] = success
                if success:
                    print(f"Decreased {account_id}: equity £{equity:,.2f} (tier {int(equity // 3500)}) -> multiplier {current_multiplier} -> {target_multiplier}")
            else:
                print(f"No change needed for {account_id}: equity £{equity:,.2f} (tier {int(equity // 3500)}) -> multiplier {current_multiplier}")

            results.append(result)

        return results

    except Exception as e:
        print(f"Error processing auto compounding accounts: {e}")
        return []

async def daily_compounding_check():
    """
    Run the compounding check daily at 22:30 GMT
    """
    while True:
        now = datetime.now(timezone.utc)

        next_run = now.replace(hour=3, minute=9, second=0, microsecond=0)
        if now >= next_run:
            next_run = next_run.replace(day=next_run.day + 1)

        seconds_until_run = (next_run - now).total_seconds()

        print(f"Waiting {seconds_until_run/3600:.1f} hours until next 22:30 GMT compounding check")
        await asyncio.sleep(seconds_until_run)

        print(f"Running auto compounding process at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        results = await process_auto_compounding_accounts()

        # Log results
        for result in results:
            print(f"Account {result['account_id']} ({result['name']}): "
                  f"Equity: £{result['equity']:,.2f}, "
                  f"Tier: {result['equity_tier']}, "
                  f"Multiplier: {result['current_multiplier']} -> {result['target_multiplier']}, "
                  f"Updated: {result['updated']}")

async def start_daily_scheduler():
    """Start the daily scheduler task for GMT"""
    task = asyncio.create_task(daily_compounding_check())
    return task

async def test_auto_compounding():
    """Test the auto compounding process immediately"""
    print("Testing auto compounding process...")
    results = await process_auto_compounding_accounts()
    print("\nTest results:")
    for result in results:
        print(f"Account {result['account_id']} ({result['name']}):")
        print(f"  Equity: £{result['equity']:,.2f} (Tier {result['equity_tier']})")
        print(f"  Multiplier: {result['current_multiplier']} -> {result['target_multiplier']}")
        print(f"  Updated: {result['updated']}\n")
    return results
