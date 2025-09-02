import asyncio

from routes.confirmAccount import confirm_account
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (Application, CommandHandler, ContextTypes,
                          ConversationHandler, MessageHandler, filters)

ACCOUNT_NUMBER_STATE, ACCOUNT_PASSWORD_STATE, CONFIRMATION_STATE = range(3)



async def connectAccount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Please provide your account number or press /exit if this was a mistake:")
    return ACCOUNT_NUMBER_STATE

async def handle_accountNum(update: Update, context: ContextTypes.DEFAULT_TYPE):
    accountNum = update.message.text
    context.user_data['Account_Number'] = accountNum
    await update.message.reply_text(f"Please provide the password for account number: {accountNum} or press /exit to exit")
    return ACCOUNT_PASSWORD_STATE

async def handle_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    accountPassword = update.message.text
    context.user_data['Account_Password'] = accountPassword

    # Create Yes/No keyboard
    keyboard = [["Yes", "No"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    # Combine all text into a single string
    message_text = (
        f"You have provided these details:\n"
        f"Account Number: {context.user_data.get('Account_Number')}\n"
        f"Account Password: {context.user_data.get('Account_Password')}\n\n"
        f"Does this look correct? (Tap buttons or use /yes or /no)\n\n"
        f"(Buttons can be found under the ⌘ button)"
    )

    await update.message.reply_text(
        message_text,
        reply_markup=reply_markup
    )
    return CONFIRMATION_STATE

async def handle_yes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    login = context.user_data['Account_Number']
    password = context.user_data['Account_Password']
    confirmation_id = await confirm_account(login=login, password=password)
    if confirmation_id:
        await update.message.reply_text(
            "Great! Account connection confirmed.",
            reply_markup=ReplyKeyboardRemove()
        )
        context.user_data.clear()
        return ConversationHandler.END
    else:
        await update.message.reply_text("Sorry we couldnt find those details, try again via /connectAccount")

async def handle_no(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Okay, let's start over. Please provide your account number: \n\nOr Press /exit to exit the process",
        reply_markup=ReplyKeyboardRemove()
    )
    context.user_data.clear()
    return ACCOUNT_NUMBER_STATE

async def handle_invalid_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Please tap Yes/No buttons or use /yes or /no commands. (Buttons can be found under the ⌘ button)")
    return CONFIRMATION_STATE

async def exit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "Process cancelled. See you later!",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

connectAccount_conversation = ConversationHandler(
    entry_points=[CommandHandler("connectAccount", connectAccount)],
    states={
        ACCOUNT_NUMBER_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_accountNum)],
        ACCOUNT_PASSWORD_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_password)],
        CONFIRMATION_STATE: [
            CommandHandler("yes", handle_yes),                    # /yes command
            CommandHandler("no", handle_no),                     # /no command
            MessageHandler(filters.Regex("^Yes$"), handle_yes),  # "Yes" button
            MessageHandler(filters.Regex("^No$"), handle_no),    # "No" button
            MessageHandler(filters.ALL, handle_invalid_confirmation)  # Everything else
        ]
    },
    fallbacks=[CommandHandler("exit", exit)]
)
