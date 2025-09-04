# main.py
import asyncio
# main.py (bare bones Telegram bot)
import os

from commands.adjustMultiplier import adjust_multiplier_conversation
from commands.checkAccountStatus import check_account_status_conversation
from commands.connectAccount import connectAccount_conversation
from commands.removeAccount import remove_account_conversation
from commands.start import start_command
from commands.turnAllAccounts import (turn_off_all_accounts_conversation,
                                      turn_on_all_accounts_conversation)
from commands.turnOffAccount import turn_off_account_conversation
from commands.turnOnAccount import turn_on_account_conversation
from dotenv import load_dotenv
from telegram import BotCommand, Update
from telegram.ext import (Application, CommandHandler, ContextTypes,
                          ConversationHandler, MessageHandler, filters)

load_dotenv()


async def setup_bot_commands(application):
    """Set up bot commands for autocomplete"""
    commands = [
        BotCommand("connectaccount", "Connect your trading account"),
        BotCommand("checkaccountstatus", "View account balance and status"),
        BotCommand("adjustmultiplier", "View and Adjust the multiplier on your account"),
        BotCommand("removeaccount", "Disconnect an account"),
        BotCommand("turnonaccount", "Enable a specific account"),
        BotCommand("turnoffaccount", "Disable a specific account"),
        BotCommand("turnonallaccounts", "Enable all accounts"),
        BotCommand("turnofallaccounts", "Disable all accounts"),
    ]

    await application.bot.set_my_commands(commands)


TEST_WAITING = 1


BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

bot_app = Application.builder().token(BOT_TOKEN).build()


async def async_main():
    await bot_app.initialize()
    bot_app.add_handler(connectAccount_conversation)
    bot_app.add_handler(remove_account_conversation)
    bot_app.add_handler(check_account_status_conversation)
    bot_app.add_handler(adjust_multiplier_conversation)
    bot_app.add_handler(turn_off_account_conversation)
    bot_app.add_handler(turn_on_account_conversation)

    bot_app.add_handler(turn_on_all_accounts_conversation)
    bot_app.add_handler(turn_off_all_accounts_conversation)

    bot_app.add_handler(CommandHandler("start", start_command))

    await setup_bot_commands(bot_app)

    await bot_app.start()
    await bot_app.updater.start_polling()
    print("🤖 Telegram Bot is running...")
    stop_event = asyncio.Event()
    await stop_event.wait()
    await bot_app.updater.stop()
    await bot_app.stop()
    await bot_app.shutdown()

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(async_main())
    print("Bot has shut down.")
    print("Bot has shut down.")
    print("Bot has shut down.")
    print("Bot has shut down.")
