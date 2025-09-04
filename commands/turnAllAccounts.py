import asyncio

from config import db
from routes.toggleAccountStatus import disable_account, enable_account
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (CallbackQueryHandler, CommandHandler, ContextTypes,
                          ConversationHandler)

# States
CONFIRM_ENABLE_ALL = 1
CONFIRM_DISABLE_ALL = 2

async def start_turn_on_all_accounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point - confirm turning on all accounts"""
    user_id = str(update.effective_user.id)

    # Get accounts from DB
    row = db.table('algo-accounts').select("*").eq('telegramId', user_id).execute()

    if not row.data:
        await update.message.reply_text("No accounts found!")
        return ConversationHandler.END

    accounts = row.data[0].get("accounts", [])

    if not accounts:
        await update.message.reply_text("No accounts found!")
        return ConversationHandler.END

    # Create list of account names
    account_list = ""
    for i, account in enumerate(accounts, 1):
        login = account.get('login', f'Account {i}')
        account_list += f"{i}. {login}\n"

    # Create confirmation buttons
    keyboard = [
        [InlineKeyboardButton("Yes, Turn On All", callback_data="confirm_enable_all")],
        [InlineKeyboardButton("Cancel", callback_data="cancel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"Are you sure you want to turn ON all {len(accounts)} accounts?\n\n"
        f"<b>Connected Accounts:</b>\n{account_list}\n"
        f"This action will enable all your connected accounts.",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    return CONFIRM_ENABLE_ALL

async def handle_enable_all_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle confirmation and enable all accounts"""
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        await query.edit_message_text("Turn on all accounts cancelled.")
        return ConversationHandler.END

    if query.data == "confirm_enable_all":
        user_id = str(update.effective_user.id)

        # Get fresh account data
        row = db.table('algo-accounts').select("*").eq('telegramId', user_id).execute()
        accounts = row.data[0].get("accounts", [])

        await query.edit_message_text(f"Turning on {len(accounts)} accounts...")

        # Enable all accounts and track results
        results = []
        successful = 0
        failed = 0

        for account in accounts:
            account_id = account.get('accountId', '')
            account_login = account.get('login', 'Unknown')

            result = await enable_account(account_id)
            if result:
                successful += 1
                results.append(f"✅ <b>{account_login}:</b> Enabled")
            else:
                failed += 1
                results.append(f"❌ <b>{account_login}:</b> Failed")

        # Create detailed results message
        results_text = "\n".join(results)
        result_message = (
            f"<b>Bulk Enable Complete</b>\n\n"
            f"<b>Results:</b>\n{results_text}\n\n"
            f"<b>Summary:</b>\n"
            f"Total: {len(accounts)} | Success: {successful} | Failed: {failed}"
        )

        await query.edit_message_text(result_message, parse_mode='HTML')

    return ConversationHandler.END


async def start_turn_off_all_accounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point - confirm turning off all accounts"""
    user_id = str(update.effective_user.id)

    # Get accounts from DB
    row = db.table('algo-accounts').select("*").eq('telegramId', user_id).execute()

    if not row.data:
        await update.message.reply_text("No accounts found!")
        return ConversationHandler.END

    accounts = row.data[0].get("accounts", [])

    if not accounts:
        await update.message.reply_text("No accounts found!")
        return ConversationHandler.END

    # Create list of account names
    account_list = ""
    for i, account in enumerate(accounts, 1):
        login = account.get('login', f'Account {i}')
        account_list += f"{i}. {login}\n"

    # Create confirmation buttons
    keyboard = [
        [InlineKeyboardButton("Yes, Turn Off All", callback_data="confirm_disable_all")],
        [InlineKeyboardButton("Cancel", callback_data="cancel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"Are you sure you want to turn OFF all {len(accounts)} accounts?\n\n"
        f"<b>Connected Accounts:</b>\n{account_list}\n"
        f"This action will disable all your connected accounts.",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    return CONFIRM_DISABLE_ALL

async def handle_disable_all_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle confirmation and disable all accounts"""
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        await query.edit_message_text("Turn off all accounts cancelled.")
        return ConversationHandler.END

    if query.data == "confirm_disable_all":
        user_id = str(update.effective_user.id)

        # Get fresh account data
        row = db.table('algo-accounts').select("*").eq('telegramId', user_id).execute()
        accounts = row.data[0].get("accounts", [])

        await query.edit_message_text(f"Turning off {len(accounts)} accounts...")

        # Disable all accounts and track results
        results = []
        successful = 0
        failed = 0

        for account in accounts:
            account_id = account.get('accountId', '')
            account_login = account.get('login', 'Unknown')

            result = await disable_account(account_id)
            if result:
                successful += 1
                results.append(f"✅ <b>{account_login}:</b> Disabled")
            else:
                failed += 1
                results.append(f"❌ <b>{account_login}:</b> Failed")

        # Create detailed results message
        results_text = "\n".join(results)
        result_message = (
            f"<b>Bulk Disable Complete</b>\n\n"
            f"<b>Results:</b>\n{results_text}\n\n"
            f"<b>Summary:</b>\n"
            f"Total: {len(accounts)} | Success: {successful} | Failed: {failed}"
        )

        await query.edit_message_text(result_message, parse_mode='HTML')

    return ConversationHandler.END

async def cancel_bulk_operation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel bulk operations"""
    await update.message.reply_text("Bulk operation cancelled.")
    return ConversationHandler.END

# Create ConversationHandlers
turn_on_all_accounts_conversation = ConversationHandler(
    entry_points=[CommandHandler("turnOnAllAccounts", start_turn_on_all_accounts)],
    states={
        CONFIRM_ENABLE_ALL: [CallbackQueryHandler(handle_enable_all_confirmation)]
    },
    fallbacks=[CommandHandler("cancel", cancel_bulk_operation)]
)

turn_off_all_accounts_conversation = ConversationHandler(
    entry_points=[CommandHandler("turnOffAllAccounts", start_turn_off_all_accounts)],
    states={
        CONFIRM_DISABLE_ALL: [CallbackQueryHandler(handle_disable_all_confirmation)]
    },
    fallbacks=[CommandHandler("cancel", cancel_bulk_operation)]
)

# Add to your main.py:
# app.add_handler(turn_on_all_accounts_conversation)
# app.add_handler(turn_off_all_accounts_conversation)
