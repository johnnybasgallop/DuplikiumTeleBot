from config import db
from routes.toggleAccountStatus import enable_account
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (CallbackQueryHandler, CommandHandler, ContextTypes,
                          ConversationHandler)

# State
SELECT_ACCOUNT_TO_ENABLE = 1

async def start_turn_on_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point - show accounts to enable"""
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
            text=f"Turn On {login}",
            callback_data=f"enable_{i}"
        )])

    # Add cancel option
    keyboard.append([InlineKeyboardButton("Cancel", callback_data="cancel")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"Select account to turn on:\n\nYou have {len(accounts)} accounts:",
        reply_markup=reply_markup
    )
    return SELECT_ACCOUNT_TO_ENABLE

async def handle_account_enable(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle account selection and enable it"""
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        await query.edit_message_text("Account enable cancelled.")
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

    # Get the account to enable
    account_to_enable = accounts[account_index]
    account_id = account_to_enable.get('accountId', '')
    account_login = account_to_enable.get('login', 'Unknown')

    # Show loading message
    await query.edit_message_text(f"Turning on account {account_login}...")

    # Call the enable API route
    result = await enable_account(account_id)

    if result:
        await query.edit_message_text(
            f"<b>Account Turned On Successfully</b>\n\n"
            f"<b>Account:</b> {account_login}\n"
            f"<b>Status:</b> Enabled\n"
            f"<b>ID:</b> <code>{account_id}</code>",
            parse_mode='HTML'
        )
    else:
        await query.edit_message_text(f"Failed to turn on account {account_login}")

    return ConversationHandler.END

async def cancel_enable(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the enable process"""
    await update.message.reply_text("Account enable cancelled.")
    return ConversationHandler.END

# Create ConversationHandler
turn_on_account_conversation = ConversationHandler(
    entry_points=[CommandHandler("turnOnAccount", start_turn_on_account)],
    states={
        SELECT_ACCOUNT_TO_ENABLE: [CallbackQueryHandler(handle_account_enable)]
    },
    fallbacks=[CommandHandler("cancel", cancel_enable)]
)

# Add to your main.py:
# app.add_handler(turn_on_account_conversation)
