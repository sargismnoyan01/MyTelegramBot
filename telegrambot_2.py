
import logging
from telegram import Update, ForceReply, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler, CallbackQueryHandler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

NAME, GAME_ID, PHONE_NUMBER, AMOUNT, TRANSFER_METHOD, TRANSFER_CONFIRMATION, PICTURE = range(7)

applications = {}

async def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("Ma'lumotlarni kiriting", callback_data='enter_data')],

    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(
            "Salom👋. 🐼 My bot ga xush kelibsiz",
            reply_markup=reply_markup
        )
    elif update.callback_query:
        await update.callback_query.message.reply_text(
            "🐼 My bot ga xush kelibsiz",
            reply_markup=reply_markup
        )

async def enter_data(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()

    user = query.from_user
    await query.message.reply_html(
        rf'👤 Iltimos, ismingiz va familiyangizni kiriting ',
        reply_markup=ForceReply(selective=True),
    )
    return NAME

async def name(update: Update, context: CallbackContext) -> int:
    context.user_data['name'] = update.message.text
    await update.message.reply_text("🆔 Melbet hisob ID raqamini yuboring.")
    return GAME_ID

async def game_id(update: Update, context: CallbackContext) -> int:
    context.user_data['game_id'] = update.message.text
    await update.message.reply_text("📱 +374* raqamini yuboring.")
    return PHONE_NUMBER

async def phone_number(update: Update, context: CallbackContext) -> int:
    context.user_data['phone_number'] = update.message.text
    await update.message.reply_text("🏦 To’ldirish summasini yozing.")
    return AMOUNT

async def amount(update: Update, context: CallbackContext) -> int:
    context.user_data['amount'] = update.message.text

    keyboard = [
        [InlineKeyboardButton("💳 VISA", callback_data='VISA')],
        [InlineKeyboardButton("💳 MASTER", callback_data='MASTER')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("🧾 O’tkazma turini tanlang.", reply_markup=reply_markup)
    return TRANSFER_METHOD

async def transfer_method(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    choice = query.data

    if choice == 'VISA':
        await query.message.reply_text("VISA kartasi tanlandi: 9860030101191978")
    elif choice == 'MASTER':
        await query.message.reply_text("MASTER kartasi tanlandi: 8600020783405728")

    context.user_data['transfer_method'] = choice

    keyboard = [
        [InlineKeyboardButton("✅ha", callback_data='transferred')],
        [InlineKeyboardButton("❌yo'q", callback_data='not_transferred')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text("Pul o'tkazildimi?", reply_markup=reply_markup)
    return TRANSFER_CONFIRMATION

async def transfer_confirmation(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    choice = query.data

    if choice == 'not_transferred':
        await start(update, context)
        return ConversationHandler.END
    
    context.user_data['transfer_confirmation'] = choice

    await query.message.reply_text("🧾 O'tkazma chekni yuboring.")
    return PICTURE

async def picture(update: Update, context: CallbackContext) -> int:
    context.user_data['picture'] = update.message.photo[-1].file_id
    user_data = context.user_data

    application_id = f"{user_data['game_id']}-{update.effective_chat.id}"
    applications[application_id] = user_data

    recipient_chat_id = 'Your ID'
    user_data['user_chat_id'] = update.effective_chat.id

    keyboard = [
        [InlineKeyboardButton("Tasdiqlang", callback_data=f'approve_{application_id}')],
        [InlineKeyboardButton("Rad etish", callback_data=f'reject_{application_id}')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await context.bot.send_photo(
            chat_id=recipient_chat_id,
            photo=user_data['picture'],
            caption=f"Application received:\n\n"
                    f"Nomi: {user_data['name']}\nID: {user_data['game_id']}\nTelefon raqami: {user_data['phone_number']}\nMiqdori: {user_data['amount']}\nO'tkazish usuli: {user_data['transfer_method']}\nTransferni tasdiqlash: {user_data['transfer_confirmation']}\n\n",
            reply_markup=reply_markup
        )
        await update.message.reply_text("⌛️ So’rovingiz yuborildi, Tasdiqlanishini kuting")
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        await update.message.reply_text("There was an error sending your details for approval.")

    await update.message.reply_text(
        "Iltimos, ma'lumotlarni kiritish uchun tugmani bosing.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Ma'lumotlarni kiriting", callback_data='enter_data')]
        ])
    )

    return ConversationHandler.END

async def handle_approval(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    callback_data = query.data

    action, application_id = callback_data.split('_')
    if application_id in applications:
        user_data = applications[application_id]
        user_chat_id = user_data['user_chat_id']

        if action == 'approve':
            await context.bot.send_message(
                chat_id=user_chat_id,
                text=f"✅ Kutganingiz uchun rahmat, arizangiz tasdiqlandi ✅\n\n"
                     f"Ism: {user_data['name']}\nID: {user_data['game_id']}\nTelefon raqami: {user_data['phone_number']}\nMiqdori: {user_data['amount']}\nO'tkazish usuli: {user_data['transfer_method']}\nTransferni tasdiqlash: {user_data['transfer_confirmation']}"
            )
            await query.edit_message_text(f"Application {application_id} approved.")
        elif action == 'reject':
            await context.bot.send_message(
                chat_id=user_chat_id,
                text="❌ Rad etildi, admin bilan bog'laning"
            )
            await query.edit_message_text(f"Application {application_id} rejected.")
        
        del applications[application_id]

        # Remove buttons by editing the message and setting reply_markup to None
        await query.edit_message_reply_markup(reply_markup=None)

        await context.bot.send_message(
            chat_id=user_chat_id,
            text="▶️ Iltimos, ma'lumotlarni kiritish uchun tugmani bosing.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Ma'lumotlarni kiriting", callback_data='enter_data')]
            ])
        )
    else:
        await query.edit_message_text("Application not found.")

async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Operation cancelled.")
    return ConversationHandler.END

async def get_chat_id(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    await update.message.reply_text(f'This chat ID is: {chat_id}')

def main() -> None:
    TOKEN = 'YOUR TOKEN'

    application = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(enter_data, pattern='enter_data')],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name)],
            GAME_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, game_id)],
            PHONE_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, phone_number)],
            AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, amount)],
            TRANSFER_METHOD: [CallbackQueryHandler(transfer_method)],
            TRANSFER_CONFIRMATION: [CallbackQueryHandler(transfer_confirmation)],
            PICTURE: [MessageHandler(filters.PHOTO, picture)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(handle_approval, pattern='approve_|reject_'))
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("get_chat_id", get_chat_id))

    application.run_polling()

if __name__ == '__main__':
    main()

