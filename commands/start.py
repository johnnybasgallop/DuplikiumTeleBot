from telegram import Update
from telegram.ext import CommandHandler, ContextTypes


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome message with all available commands"""

    welcome_message = (
        f"<b>Getting Started</b>\n\n"
        f"1. Contact an admin to set up your algo account\n"
        f"2. Use /connectaccount to link your account to this bot\n"
        f"3. Use /checkaccountstatus to verify connection\n"
        f"4. Use control commands to manage trading activity\n\n"

        f"<b>Security</b>\n"
        f"Your credentials are transmitted securely and not stored permanently."
        f"You can control me by sending these commands:\n\n"

        f"/connectaccount - connect your existing algo account\n"
        f"/checkaccountstatus - view account balance and status\n"
        f"/removeaccount - disconnect an account\n\n"

        f"<b>Account Control</b>\n"
        f"/turnonaccount - enable a specific account\n"
        f"/turnoffaccount - disable a specific account\n"
        f"/turnonallaccounts - enable all accounts\n"
        f"/turnofallaccounts - disable all accounts\n\n"

        f"<b>Risk Management</b>\n"
        f"<b>When possible auto compounding adds another algo to the account to compound/reinvest profits</b>\n\n"
        f"/turnonautocompounding - enable auto compounding\n"
        f"/turnoffautocompounding - disable auto compounding\n"

    )

    await update.message.reply_text(welcome_message, parse_mode='HTML')
