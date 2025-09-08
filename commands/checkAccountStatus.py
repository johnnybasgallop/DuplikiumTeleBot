from config import db
from routes.getMulti import get_account_multiplier
from routes.getStatus import get_account_info
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (CallbackQueryHandler, CommandHandler, ContextTypes,
                          ConversationHandler)

# State
SELECT_ACCOUNT_TO_CHECK = 1

async def get_account_info_with_multiplier(account_id: str) -> str:
    """
    Get account info including multiplier data with proper number formatting
    """
    # Get basic account info
    account_info = await get_account_info(account_id)

    # Get multiplier info
    multiplier_data = await get_account_multiplier(account_id)

    if multiplier_data and multiplier_data.get("multiplier_value") is not None:
        try:
            # Convert to float first, then format
            multiplier_value = float(multiplier_data["multiplier_value"])

            # Format multiplier to remove unnecessary decimals
            if multiplier_value == int(multiplier_value):
                formatted_multiplier = str(int(multiplier_value))
            else:
                formatted_multiplier = f"{multiplier_value:.1f}".rstrip('0').rstrip('.')

            multiplier_text = f"⚖️ <b>Current Multiplier:</b> {formatted_multiplier}"
        except (ValueError, TypeError):
            # Handle case where multiplier_value can't be converted
            multiplier_text = f"⚖️ <b>Current Multiplier:</b> {multiplier_data['multiplier_value']}"
    else:
        multiplier_text = "⚖️ <b>Current Multiplier:</b> Not Set"

    # Combine account info with multiplier
    return f"{account_info}\n{multiplier_text}"

async def start_check_account_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    """Entry point - show accounts to check status"""
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
            text=f"📊 {login}",
            callback_data=f"check_{i}"
        )])

    # Add check all option
    keyboard.append([InlineKeyboardButton("📊 Check All Accounts", callback_data="check_all")])

    # Add cancel option
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"Select account to check status:\n\nYou have {len(accounts)} accounts:",
        reply_markup=reply_markup
    )
    return SELECT_ACCOUNT_TO_CHECK

async def handle_account_status_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle account selection and show status"""
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        await query.edit_message_text("✅ Account status check cancelled.")
        return ConversationHandler.END

    if query.data == "check_all":
        # Handle checking all accounts - send individual messages
        user_id = str(update.effective_user.id)

        # Get fresh account data
        row = db.table('algo-accounts').select("*").eq('telegramId', user_id).execute()
        accounts = row.data[0].get("accounts", [])

        await query.edit_message_text(f"Checking status for all {len(accounts)} accounts...")

        # Send individual message for each account
        for i, account in enumerate(accounts):
            account_id = account.get('accountId', '')
            login = account.get('login', f'Account {i+1}')

            try:
                account_info = await get_account_info_with_multiplier(account_id)

                # Send individual message for each account
                await update.callback_query.message.reply_text(
                    account_info,
                    parse_mode="HTML"
                )

            except Exception as e:
                # Send error message for failed account
                await update.callback_query.message.reply_text(
                    f"❌ Failed to get status for account {login}: {str(e)}"
                )

        # Send completion message
        await update.callback_query.message.reply_text(
            f"✅ Status check completed for all {len(accounts)} accounts."
        )

        return ConversationHandler.END

    # Handle individual account check
    account_index = int(query.data.split("_")[1])
    user_id = str(update.effective_user.id)

    # Get fresh account data
    row = db.table('algo-accounts').select("*").eq('telegramId', user_id).execute()
    accounts = row.data[0].get("accounts", [])

    if account_index >= len(accounts):
        await query.edit_message_text("❌ Account not found!")
        return ConversationHandler.END

    # Get the account to check
    account_to_check = accounts[account_index]
    account_id = account_to_check.get('accountId', '')

    # Show loading message
    await query.edit_message_text("Checking account status...")

    # Get account info with multiplier
    account_info = await get_account_info_with_multiplier(account_id)

    # Show the results
    await query.edit_message_text(account_info, parse_mode="HTML")

    return ConversationHandler.END

async def cancel_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the status check process"""
    await update.message.reply_text("✅ Account status check cancelled.")
    return ConversationHandler.END

# Create ConversationHandler
check_account_status_conversation = ConversationHandler(
    entry_points=[CommandHandler("checkAccountStatus", start_check_account_status)],
    states={
        SELECT_ACCOUNT_TO_CHECK: [CallbackQueryHandler(handle_account_status_check)]
    },
    fallbacks=[CommandHandler("cancel", cancel_check)]
)
