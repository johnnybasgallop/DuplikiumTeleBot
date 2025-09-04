from config import db
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (CallbackQueryHandler, CommandHandler, ContextTypes,
                          ConversationHandler)

# State
SELECT_ACCOUNT_TO_DELETE = 1

async def start_remove_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point - show accounts to delete"""
    user_id = str(update.effective_user.id)

    # Get accounts from DB
    row = db.table('algo-accounts').select("*").eq('telegramId', user_id).execute()

    if not row.data:
        await update.message.reply_text("❌ No accounts found!")
        return ConversationHandler.END

    accounts = row.data[0].get("accounts", [])

    if not accounts:
        await update.message.reply_text("❌ No accounts found!")
        return ConversationHandler.END

    # Create clickable buttons for each account
    keyboard = []
    for i, account in enumerate(accounts):
        login = account.get('login', f'Account {i+1}')
        keyboard.append([InlineKeyboardButton(
            text=f"🗑️ {login}",
            callback_data=f"delete_{i}"
        )])

    # Add cancel option
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"Select account to remove:\n\nYou have {len(accounts)} accounts:",
        reply_markup=reply_markup
    )
    return SELECT_ACCOUNT_TO_DELETE

async def handle_account_deletion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle account selection and delete it"""
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        await query.edit_message_text("✅ Account removal cancelled.")
        return ConversationHandler.END

    # Get account index from callback data
    account_index = int(query.data.split("_")[1])
    user_id = str(update.effective_user.id)

    # Get fresh account data
    row = db.table('algo-accounts').select("*").eq('telegramId', user_id).execute()
    accounts = row.data[0].get("accounts", [])

    if account_index >= len(accounts):
        await query.edit_message_text("❌ Account not found!")
        return ConversationHandler.END

    # Get the account to delete
    account_to_delete = accounts[account_index]
    account_login = account_to_delete.get('login', 'Unknown')

    # Remove from array
    accounts.pop(account_index)

    # Update database
    result = db.table("algo-accounts").update({
        "accounts": accounts
    }).eq('telegramId', user_id).execute()

    if result.data:
        await query.edit_message_text(f"🗑️ Disconnected Account: {account_login}")
    else:
        await query.edit_message_text(f"❌ Failed to delete account: {account_login}")

    return ConversationHandler.END

async def cancel_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the removal process"""
    await update.message.reply_text("✅ Account removal cancelled.")
    return ConversationHandler.END

# Create ConversationHandler
remove_account_conversation = ConversationHandler(
    entry_points=[CommandHandler("removeAccount", start_remove_account)],
    states={
        SELECT_ACCOUNT_TO_DELETE: [CallbackQueryHandler(handle_account_deletion)]
    },
    fallbacks=[CommandHandler("cancel", cancel_remove)]
)

# Add to your main.py:
# app.add_handler(remove_account_conversation)
