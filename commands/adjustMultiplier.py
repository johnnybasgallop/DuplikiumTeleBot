from config import db
from routes.getMulti import get_account_multiplier
from routes.getStatus import check_account_details
from routes.setMulti import update_multiplier_with_confirmation
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (CallbackQueryHandler, CommandHandler, ContextTypes,
                          ConversationHandler, MessageHandler, filters)

# States
SELECT_ACCOUNT_TO_ADJUST, ENTER_NEW_MULTIPLIER = range(2)

async def start_adjust_multiplier(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    """Entry point - show accounts to adjust multiplier"""
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
            text=f"Adjust {login}",
            callback_data=f"adjust_{i}"
        )])

    # Add cancel option
    keyboard.append([InlineKeyboardButton("Cancel", callback_data="cancel")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"Select account to adjust multiplier:\n\nYou have {len(accounts)} accounts:",
        reply_markup=reply_markup
    )
    return SELECT_ACCOUNT_TO_ADJUST

async def handle_account_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle account selection and show current multiplier/balance"""
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        await query.edit_message_text("Multiplier adjustment cancelled.")
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

    # Get the selected account
    selected_account = accounts[account_index]
    account_id = selected_account.get('accountId', '')
    account_login = selected_account.get('login', 'Unknown')

    # Store account info for next step
    context.user_data['selected_account_id'] = account_id
    context.user_data['selected_account_login'] = account_login

    await query.edit_message_text("Getting account information...")

    # Get current multiplier and account balance
    multiplier_data = await get_account_multiplier(account_id)
    account_details = await check_account_details(account_id)

    if not account_details:
        await query.edit_message_text("Failed to retrieve account details.")
        return ConversationHandler.END

    current_multiplier = "Not Set"
    if multiplier_data and multiplier_data.get("multiplier_value") is not None:
        current_multiplier = str(multiplier_data["multiplier_value"])

    balance = account_details.get("balance", 0)

    # Create cancel button for this step
    keyboard = [[InlineKeyboardButton("Cancel", callback_data="cancel_input")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"<b>Adjust Multiplier</b>\n\n"
        f"<b>Account:</b> {account_login}\n"
        f"<b>Current Balance:</b> <code>${balance:,.2f}</code>\n"
        f"<b>Current Multiplier:</b> {current_multiplier}\n\n"
        f"What would you like your new multiplier to be?\n"
        f"<i>Please enter a number (e.g., 1.5, 2.0, 0.5)</i>",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    return ENTER_NEW_MULTIPLIER

async def handle_new_multiplier(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle new multiplier input"""
    try:
        new_multiplier = float(update.message.text)

        if new_multiplier <= 0:
            await update.message.reply_text("Multiplier must be greater than 0. Please try again.")
            return ENTER_NEW_MULTIPLIER

        account_id = context.user_data['selected_account_id']
        account_login = context.user_data['selected_account_login']

        await update.message.reply_text(f"Setting multiplier to {new_multiplier} for {account_login}...")

        # Set the new multiplier
        result_message = await update_multiplier_with_confirmation(account_id, new_multiplier)

        await update.message.reply_text(result_message, parse_mode='HTML')

        # Clean up context
        context.user_data.clear()
        return ConversationHandler.END

    except ValueError:
        await update.message.reply_text("Invalid number format. Please enter a valid number (e.g., 1.5, 2.0).")
        return ENTER_NEW_MULTIPLIER

async def handle_cancel_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle cancel button during input"""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text("Multiplier adjustment cancelled.")
    context.user_data.clear()
    return ConversationHandler.END

async def cancel_adjust(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the adjustment process"""
    await update.message.reply_text("Multiplier adjustment cancelled.")
    context.user_data.clear()
    return ConversationHandler.END

# Create ConversationHandler
adjust_multiplier_conversation = ConversationHandler(
    entry_points=[CommandHandler("adjustMultiplier", start_adjust_multiplier)],
    states={
        SELECT_ACCOUNT_TO_ADJUST: [CallbackQueryHandler(handle_account_selection)],
        ENTER_NEW_MULTIPLIER: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_new_multiplier),
            CallbackQueryHandler(handle_cancel_input, pattern="^cancel_input$")
        ]
    },
    fallbacks=[CommandHandler("cancel", cancel_adjust)]
)

# Add to your main.py:
# app.add_handler(adjust_multiplier_conversation)
