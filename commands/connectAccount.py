import asyncio

from config import db
from routes.confirmAccount import confirm_account
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (Application, CallbackQueryHandler, CommandHandler,
                          ContextTypes, ConversationHandler, MessageHandler,
                          filters)

ACCOUNT_NUMBER_STATE, ACCOUNT_PASSWORD_STATE, CONFIRMATION_STATE = range(3)

async def connectAccount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    # Add Cancel button to first message
    keyboard = [[InlineKeyboardButton("Cancel", callback_data="cancel")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Please provide your account number:",
        reply_markup=reply_markup
    )
    return ACCOUNT_NUMBER_STATE

async def handle_accountNum(update: Update, context: ContextTypes.DEFAULT_TYPE):
    accountNum = update.message.text
    context.user_data['Account_Number'] = accountNum

    # Add Cancel button to password request
    keyboard = [[InlineKeyboardButton("Cancel", callback_data="cancel")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"Please provide the password for account number: {accountNum}",
        reply_markup=reply_markup
    )
    return ACCOUNT_PASSWORD_STATE

async def handle_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    accountPassword = update.message.text
    context.user_data['Account_Password'] = accountPassword

    # Create inline keyboard with Yes, No, and Cancel
    keyboard = [
        [InlineKeyboardButton("Yes", callback_data="confirm_yes")],
        [InlineKeyboardButton("No", callback_data="confirm_no")],
        [InlineKeyboardButton("Cancel", callback_data="cancel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message_text = (
        f"You have provided these details:\n"
        f"Account Number: {context.user_data.get('Account_Number')}\n"
        f"Account Password: {context.user_data.get('Account_Password')}\n\n"
        f"Does this look correct?"
    )

    await update.message.reply_text(
        message_text,
        reply_markup=reply_markup
    )
    return CONFIRMATION_STATE

async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button clicks"""
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        # Handle Cancel button
        await query.edit_message_text("Process cancelled. See you later!")
        context.user_data.clear()
        return ConversationHandler.END

    elif query.data == "confirm_yes":
        # Handle Yes confirmation
        login = context.user_data['Account_Number']
        password = context.user_data['Account_Password']
        user_id = str(update.effective_user.id)

        confirmation_id = await confirm_account(login=login, password=password)

        if confirmation_id:
            new_account = {'login': login, 'accountId': confirmation_id, 'auto_compounding': False}

            # Check if user already has an account record
            row = db.table('algo-accounts').select("*").eq('telegramId', user_id).execute()

            if row.data:
                # User exists - add to existing accounts array
                existing_accounts = row.data[0].get("accounts", [])
                existing_accounts.append(new_account)

                result = db.table("algo-accounts").update({
                    "accounts": existing_accounts,
                }).eq('telegramId', user_id).execute()

                await query.edit_message_text(f"Great! Additional account connection confirmed.")

            else:
                # User doesn't exist - create new record
                result = db.table("algo-accounts").insert({
                    "telegramId": user_id,
                    "accounts": [new_account],
                }).execute()

                await query.edit_message_text("Great! First account connection confirmed.")

            context.user_data.clear()

            if result.data:
                await update.callback_query.message.reply_text("Account saved!")
            else:
                await update.callback_query.message.reply_text("Failed to save account.")

        else:
            await query.edit_message_text("Sorry we couldn't find those details, try again via /connectAccount")

        return ConversationHandler.END

    elif query.data == "confirm_no":
        # Handle No - start over
        await query.edit_message_text("Okay, let's start over. Please provide your account number:")
        context.user_data.clear()
        return ACCOUNT_NUMBER_STATE

async def handle_cancel_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Cancel button clicks in account/password states"""
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        await query.edit_message_text("Process cancelled. See you later!")
        context.user_data.clear()
        return ConversationHandler.END

# Keep /exit as fallback (optional)
async def exit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Process cancelled. See you later!")
    return ConversationHandler.END

connectAccount_conversation = ConversationHandler(
    entry_points=[CommandHandler("connectAccount", connectAccount)],
    states={
        ACCOUNT_NUMBER_STATE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_accountNum),
            CallbackQueryHandler(handle_cancel_buttons, pattern="^cancel$")
        ],
        ACCOUNT_PASSWORD_STATE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_password),
            CallbackQueryHandler(handle_cancel_buttons, pattern="^cancel$")
        ],
        CONFIRMATION_STATE: [CallbackQueryHandler(handle_confirmation, pattern="^(confirm_|cancel$)")]
    },
    fallbacks=[CommandHandler("exit", exit)]  # Optional backup
)
