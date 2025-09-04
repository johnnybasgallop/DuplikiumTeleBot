from telegram import Update
from telegram.ext import CommandHandler, ContextTypes


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome message with all available commands"""

    welcome_message = (
        f"<b>🤖 Trade Copier Bot</b>\n\n"
        f"Welcome to your automated trading account management system. "
        f"This bot helps you manage your Algo accounts directly from Telegram.\n\n"

        f"<b>📊 Account Management</b>\n"
        f"<code>/connectaccount</code> - Connect your already active algo accounts for management\n"
        f"<code>/checkaccountstatus</code> - View account balance, equity, and connection status\n"
        f"<code>/removeaccount</code> - Disconnect and remove an account\n\n"

        f"<b>⚙️ Account Control</b>\n"
        f"<code>/turnonaccount</code> - Enable a specific account for trading\n"
        f"<code>/turnoffaccount</code> - Disable a specific account\n"
        f"<code>/turnonallaccounts</code> - Enable all connected accounts at once\n"
        f"<code>/turnofallaccounts</code> - Disable all connected accounts at once\n\n"

        f"<b>📈 Risk Management</b>\n"
        f"<code>/adjustmultiplier</code> - View and modify the lot multiplier for your accounts\n\n"

        f"<b>💡 How to Get Started</b>\n"
        f"1. Use <code>/connectaccount</code> to link your first trading account\n"
        f"2. Check your account status with <code>/checkaccountstatus</code>\n"
        f"3. Adjust settings like multipliers as needed\n"
        f"4. Use enable/disable commands to control trading activity\n\n"

        f"<b>🔒 Security Note</b>\n"
        f"Your account credentials are securely processed and not stored permanently. "
        f"All commands require your Telegram user authentication.\n\n"

        f"<i>Need help? Each command provides step-by-step guidance with interactive buttons.</i>"
    )

    await update.message.reply_text(welcome_message, parse_mode='HTML')

# Add this handler to your main.py:
# application.add_handler(CommandHandler("start", start_command))
