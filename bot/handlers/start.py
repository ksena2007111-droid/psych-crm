from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
from bot.api_client import get_client_by_telegram, register_client

PSYCHOLOGIST_ID = 1  # ID психолога в БД

ASK_NAME, ASK_PHONE = range(2)

MAIN_MENU = ReplyKeyboardMarkup(
    [
        [KeyboardButton("📅 Записаться")],
        [KeyboardButton("📋 Мои записи")],
        [KeyboardButton("❌ Отменить запись")],
    ],
    resize_keyboard=True
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    client = await get_client_by_telegram(telegram_id)

    if client:
        # Проверяем что клиент не удалён (API вернул валидный объект с id)
        if client.get('id'):
            await update.message.reply_text(
                f"С возвращением, {client['name']}! 👋\nЧем могу помочь?",
                reply_markup=MAIN_MENU
            )
            return ConversationHandler.END
        
    # Клиент не найден или был удалён — начинаем регистрацию заново
    await update.message.reply_text(
        "Добро пожаловать! 👋\nДля записи на консультацию нужно зарегистрироваться.\n\n"
        "Как вас зовут?"
    )
    return ASK_NAME


async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text(
        f"Приятно познакомиться, {context.user_data['name']}! 😊\n"
        "Укажите ваш номер телефона (или напишите «пропустить»):"
    )
    return ASK_PHONE


async def finish_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text
    if phone.lower() == 'пропустить':
        phone = None

    telegram_id = update.effective_user.id
    name = context.user_data.get('name', update.effective_user.first_name)

    client = await register_client(telegram_id=telegram_id, name=name, phone=phone)

    if client:
        await update.message.reply_text(
            f"Отлично, {name}! Вы успешно зарегистрированы. ✅\n"
            "Теперь вы можете записаться на консультацию.",
            reply_markup=MAIN_MENU
        )
    else:
        await update.message.reply_text(
            "Произошла ошибка при регистрации. Попробуйте позже.",
        )
    return ConversationHandler.END


def get_start_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_phone)],
            ASK_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, finish_registration)],
        },
        fallbacks=[CommandHandler("start", start)],
    )