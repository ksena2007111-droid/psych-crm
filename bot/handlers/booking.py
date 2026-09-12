from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, CallbackQueryHandler, filters
from bot.api_client import get_services, get_slots, create_booking, get_client_by_telegram
from bot.handlers.start import MAIN_MENU, PSYCHOLOGIST_ID

SELECT_SERVICE, SELECT_DATE, SELECT_TIME, CONFIRM = range(10, 14)


async def start_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    client = await get_client_by_telegram(telegram_id)
    if not client:
        await update.message.reply_text("Сначала зарегистрируйтесь через /start")
        return ConversationHandler.END

    services = await get_services(PSYCHOLOGIST_ID)
    if not services:
        await update.message.reply_text("Нет доступных услуг. Попробуйте позже.")
        return ConversationHandler.END

    # Показываем каждую услугу с описанием отдельным блоком
    text = "💼 Доступные услуги:\n\n"
    for s in services:
        text += f"{'—' * 20}\n"
        text += f"📌 *{s['name']}*\n"
        text += f"⏱ Длительность: {s['duration_minutes']} мин\n"
        text += f"💰 Стоимость: {s['price']} BYN\n"
        text += f"🌐 Формат: {'Онлайн' if s['format'] == 'online' else 'Офлайн'}\n"
        if s.get('description'):
            text += f"📝 {s['description']}\n"
        text += "\n"

    keyboard = [[InlineKeyboardButton(
        f"{s['name']} — {s['price']} BYN",
        callback_data=f"service_{s['id']}"
    )] for s in services]

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SELECT_SERVICE


async def select_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    service_id = int(query.data.split("_")[1])
    context.user_data['service_id'] = service_id

    today = datetime.now()
    keyboard = []
    row = []
    for i in range(14):
        date = today + timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        label = date.strftime("%d.%m")
        row.append(InlineKeyboardButton(label, callback_data=f"date_{date_str}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    await query.edit_message_text(
        "📅 Выберите удобную дату:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SELECT_DATE


async def select_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    date_str = query.data.split("_")[1]
    context.user_data['date'] = date_str

    result = await get_slots(PSYCHOLOGIST_ID, date_str)
    slots = result.get("slots", [])

    # Всегда строим клавиатуру с датами (нужна и при ошибке)
    today = datetime.now()
    date_keyboard = []
    row = []
    for i in range(14):
        d = today + timedelta(days=i)
        d_str = d.strftime("%Y-%m-%d")
        label = d.strftime("%d.%m")
        row.append(InlineKeyboardButton(label, callback_data=f"date_{d_str}"))
        if len(row) == 3:
            date_keyboard.append(row)
            row = []
    if row:
        date_keyboard.append(row)

    if not slots:
        # Показываем сообщение + кнопки дат снова
        await query.edit_message_text(
            f"На {date_str} нет свободных слотов. Выберите другую дату:",
            reply_markup=InlineKeyboardMarkup(date_keyboard)
        )
        return SELECT_DATE

    # Есть слоты — показываем кнопки времени
    time_keyboard = []
    row = []
    for slot in slots:
        row.append(InlineKeyboardButton(slot, callback_data=f"time_{slot}"))
        if len(row) == 4:
            time_keyboard.append(row)
            row = []
    if row:
        time_keyboard.append(row)

    await query.edit_message_text(
        f"Выберите время на {date_str}:",
        reply_markup=InlineKeyboardMarkup(time_keyboard)
    )
    return SELECT_TIME


async def select_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    time_str = query.data.split("_")[1]
    context.user_data['time'] = time_str

    date_str = context.user_data['date']
    service_id = context.user_data['service_id']

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Подтвердить", callback_data="confirm_yes"),
            InlineKeyboardButton("❌ Отмена", callback_data="confirm_no"),
        ]
    ])

    await query.edit_message_text(
        f"Подтвердите запись:\n\n"
        f"📅 Дата: {date_str}\n"
        f"🕐 Время: {time_str}\n\n"
        f"Всё верно?",
        reply_markup=keyboard
    )
    return CONFIRM


async def confirm_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "confirm_no":
        await query.edit_message_text("Запись отменена.")
        return ConversationHandler.END

    telegram_id = update.effective_user.id
    booking = await create_booking(
        telegram_id=telegram_id,
        psychologist_id=PSYCHOLOGIST_ID,
        service_id=context.user_data['service_id'],
        date=context.user_data['date'],
        time=context.user_data['time'],
    )

    if booking:
        await query.edit_message_text(
            "✅ Запись создана!\n"
            "Ожидайте подтверждения от специалиста."
        )
    else:
        await query.edit_message_text("Произошла ошибка. Попробуйте позже.")

    return ConversationHandler.END


def get_booking_handler():
    return ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📅 Записаться$"), start_booking)],
        states={
            SELECT_SERVICE: [CallbackQueryHandler(select_service, pattern="^service_")],
            SELECT_DATE: [CallbackQueryHandler(select_date, pattern="^date_")],
            SELECT_TIME: [CallbackQueryHandler(select_time, pattern="^time_")],
            CONFIRM: [CallbackQueryHandler(confirm_booking, pattern="^confirm_")],
        },
        fallbacks=[],
    )