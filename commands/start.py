from telegram import Update
from telegram.ext import CommandHandler, ContextTypes


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome message with all available commands"""

    welcome_message = (
        f"🤖 <b>AJS Algo Bot</b>\n\n"

        f"Welcome to your automated trading account management system! "
        f"This bot helps you manage your algorithmic trading accounts directly from Telegram through a secure connection to your Trade Copier dashboard.\n\n"

        f"📊 <b>ACCOUNT MANAGEMENT</b>\n\n"

        f" /connectaccount  \n"
        f"🔗 Connect your existing algorithmic trading accounts that are already set up in Trade Copier. This links them to this bot for remote management and monitoring.\n\n"

        f" /checkaccountstatus  \n"
        f"📈 View comprehensive account information including current balance, equity levels, free margin, account status (enabled/disabled), and connection state (connected/disconnected).\n\n"

        f" /removeaccount  \n"
        f"🗑️ Safely disconnect and remove an account from bot management. This removes the account from your bot's database but does not delete it from Trade Copier.\n\n"

        f"⚙️ <b>ACCOUNT CONTROL</b>\n\n"

        f" /turnonaccount  \n"
        f"🟢 Enable trading activity for a specific account. When enabled, the account will actively copy trades from your master account according to your configured settings.\n\n"

        f" /turnoffaccount  \n"
        f"🔴 Disable trading activity for a specific account. When disabled, the account stops copying new trades but existing positions remain open.\n\n"

        f" /turnonallaccounts  \n"
        f"✅ Enable trading activity for all connected accounts simultaneously. Useful for quickly activating your entire portfolio after maintenance or analysis periods.\n\n"

        f" /turnofallaccounts  \n"
        f"❌ Disable trading activity for all connected accounts at once. Useful for quickly stopping all trading activity during high-risk market conditions or for maintenance.\n\n"

        # f"📈 <b>RISK MANAGEMENT</b>\n\n"

        # f" /adjustmultiplier  \n"
        # f"⚖️ View and modify the lot size multiplier for your accounts. The multiplier determines how trade sizes are calculated relative to the master account. For example, a multiplier of 2.0 means trades will be twice the size of the master account.\n\n"

        f"🚀 <b>GETTING STARTED</b>\n\n"

        f"To setup a new account for the algo, please speak with an admin...\n\n"

        f"1️⃣ Ensure your trading accounts are already set up and configured in the Trade Copier dashboard\n\n"

        f"2️⃣ Use  /connectaccount   to link your existing algo account to this bot for remote management\n\n"

        f"3️⃣ Use  /checkaccountstatus   to verify your account connection and review current balances\n\n"

        f"4️⃣ Adjust risk settings like multipliers using  /adjustmultiplier   based on your trading strategy\n\n"

        f"5️⃣ Use the enable/disable commands to control when accounts are actively trading\n\n"

        f"🔒 <b>SECURITY & PRIVACY</b>\n\n"

        f"🛡️ Your trading account credentials are transmitted securely and are not permanently stored by this bot. All authentication is handled through Trade Copier's official API endpoints.\n\n"

        f"🔐 Each command requires your Telegram user verification to ensure only authorized users can manage accounts.\n\n"

        f"💬 <b>SUPPORT</b>\n\n"

        f"ℹ️ Each command provides step-by-step guidance with interactive buttons to make the process straightforward. Commands will show you exactly what information is needed and confirm actions before making any changes to your trading accounts."
    )

    await update.message.reply_text(welcome_message, parse_mode='HTML')
