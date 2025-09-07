from config import db
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (CallbackQueryHandler, CommandHandler, ContextTypes,
                          ConversationHandler)

# State
SELECT_ACCOUNT_FOR_AUTO_COMPOUNDING = 1

async def start_turn_on_auto_compounding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    """Entry point - show accounts to enable auto compounding"""
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
        auto_compounding_status = account.get('auto_compounding', False)  # Note: keeping original typo
        status_text = "ON" if auto_compounding_status else "OFF"

        keyboard.append([InlineKeyboardButton(
            text=f"{login} (Auto Compounding: {status_text})",
            callback_data=f"enable_auto_{i}"
        )])

    # Add option to enable for all accounts
    keyboard.append([InlineKeyboardButton(
        text="Enable All Accounts",
        callback_data="enable_all"
    )])

    # Add cancel option
    keyboard.append([InlineKeyboardButton("Cancel", callback_data="cancel")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"Select account to enable auto compounding:\n\nYou have {len(accounts)} accounts:",
        reply_markup=reply_markup
    )
    return SELECT_ACCOUNT_FOR_AUTO_COMPOUNDING

async def handle_auto_compounding_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle account selection and enable auto compounding"""
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        await query.edit_message_text("Auto compounding setup cancelled.")
        return ConversationHandler.END

    user_id = str(update.effective_user.id)

    # Get fresh account data
    row = db.table('algo-accounts').select("*").eq('telegramId', user_id).execute()
    accounts = row.data[0].get("accounts", [])

    if query.data == "enable_all":
        # Enable auto compounding for all accounts
        updated_accounts = []
        for account in accounts:
            updated_account = account.copy()
            updated_account['auto_compounding'] = True  # Update existing field with typo
            updated_accounts.append(updated_account)

        # Update database
        result = db.table("algo-accounts").update({
            "accounts": updated_accounts
        }).eq('telegramId', user_id).execute()

        if result.data:
            await query.edit_message_text(
                f"Auto compounding enabled for all {len(accounts)} accounts!"
            )
        else:
            await query.edit_message_text("Failed to update auto compounding settings.")

        return ConversationHandler.END

    else:
        # Handle individual account selection
        account_index = int(query.data.split("_")[2])

        if account_index >= len(accounts):
            await query.edit_message_text("Account not found!")
            return ConversationHandler.END

        # Enable auto compounding for selected account
        accounts[account_index]['auto_compounding'] = True  # Update existing field with typo
        selected_login = accounts[account_index].get('login', 'Unknown')

        # Update database
        result = db.table("algo-accounts").update({
            "accounts": accounts
        }).eq('telegramId', user_id).execute()

        if result.data:
            await query.edit_message_text(
                f"Auto compounding enabled for account: {selected_login}"
            )
        else:
            await query.edit_message_text(f"Failed to enable auto compounding for {selected_login}")

        return ConversationHandler.END

async def cancel_auto_compounding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the auto compounding process"""
    await update.message.reply_text("Auto compounding setup cancelled.")
    return ConversationHandler.END

# Create ConversationHandler
turn_on_auto_compounding_conversation = ConversationHandler(
    entry_points=[CommandHandler("turnOnAutoCompounding", start_turn_on_auto_compounding)],
    states={
        SELECT_ACCOUNT_FOR_AUTO_COMPOUNDING: [CallbackQueryHandler(handle_auto_compounding_selection)]
    },
    fallbacks=[CommandHandler("cancel", cancel_auto_compounding)],
    per_message=False
)

# Add to your main.py:
# app.add_handler(turn_on_auto_compounding_conversation)
