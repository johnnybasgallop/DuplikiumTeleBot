from config import db
from routes.toggleAccountStatus import disable_account
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (CallbackQueryHandler, CommandHandler, ContextTypes,
                          ConversationHandler)

# State
SELECT_ACCOUNT_TO_DISABLE = 1

async def start_turn_off_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point - show accounts to disable"""
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

    # Create clickable buttons for each account
    keyboard = []
    for i, account in enumerate(accounts):
        login = account.get('login', f'Account {i+1}')
        keyboard.append([InlineKeyboardButton(
            text=f"Turn Off {login}",
            callback_data=f"disable_{i}"
        )])

    # Add cancel option
    keyboard.append([InlineKeyboardButton("Cancel", callback_data="cancel")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"Select account to turn off:\n\nYou have {len(accounts)} accounts:",
        reply_markup=reply_markup
    )
    return SELECT_ACCOUNT_TO_DISABLE

async def handle_account_disable(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle account selection and disable it"""
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        await query.edit_message_text("Account disable cancelled.")
        return ConversationHandler.END

    # Get account index from callback data
    account_index = int(query.data.split("_")[1])
    user_id = str(update.effective_user.id)

    # Get fresh account data
    row = db.table('algo-accounts').select("*").eq('telegramId', user_id).execute()
    accounts = row.data[0].get("accounts", [])

    if account_index >= len(accounts):
        await query.edit_message_text("Account not found!")
        return ConversationHandler.END

    # Get the account to disable
    account_to_disable = accounts[account_index]
    account_id = account_to_disable.get('accountId', '')
    account_login = account_to_disable.get('login', 'Unknown')

    # Show loading message
    await query.edit_message_text(f"Turning off account {account_login}...")

    # Call the disable API route
    result = await disable_account(account_id)

    if result:
        await query.edit_message_text(
            f"<b>Account Turned Off Successfully</b>\n\n"
            f"<b>Account:</b> {account_login}\n"
            f"<b>Status:</b> Disabled\n"
            f"<b>ID:</b> <code>{account_id}</code>",
            parse_mode='HTML'
        )
    else:
        await query.edit_message_text(f"Failed to turn off account {account_login}")

    return ConversationHandler.END

async def cancel_disable(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the disable process"""
    await update.message.reply_text("Account disable cancelled.")
    return ConversationHandler.END

# Create ConversationHandler
turn_off_account_conversation = ConversationHandler(
    entry_points=[CommandHandler("turnOffAccount", start_turn_off_account)],
    states={
        SELECT_ACCOUNT_TO_DISABLE: [CallbackQueryHandler(handle_account_disable)]
    },
    fallbacks=[CommandHandler("cancel", cancel_disable)]
)

# Add to your main.py:
# app.add_handler(turn_off_account_conversation)
