from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from bot.api_client import get_client_bookings, cancel_booking, get_client_by_telegram

CANCEL_SELECT = 20

STATUS_LABELS = {
    "pending": "⏳ Ожидает подтверждения",
    "confirmed": "✅ Подтверждено",
    "cancelled": "❌ Отменено",
}


async def my_bookings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    bookings = await get_client_bookings(telegram_id)

    active = [b for b in bookings if b['status'] != 'cancelled']
    if not active:
        await update.message.reply_text("У вас нет активных записей.")
        return

    text = "📋 Ваши записи:\n\n"
    for b in active:
        status = STATUS_LABELS.get(b['status'], b['status'])
        text += f"📅 {b['date']}, {b['time']}\nСтатус: {status}\n\n"

    await update.message.reply_text(text)


async def start_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    bookings = await get_client_bookings(telegram_id)
    active = [b for b in bookings if b['status'] != 'cancelled']

    if not active:
        await update.message.reply_text("Нет записей для отмены.")
        return ConversationHandler.END

    keyboard = [[InlineKeyboardButton(
        f"{b['date']} {b['time']} — {STATUS_LABELS.get(b['status'], b['status'])}",
        callback_data=f"cancel_{b['id']}"
    )] for b in active]

    await update.message.reply_text(
        "Выберите запись для отмены:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CANCEL_SELECT


async def do_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    booking_id = int(query.data.split("_")[1])

    success = await cancel_booking(booking_id)
    if success:
        await query.edit_message_text("✅ Запись отменена.")
    else:
        await query.edit_message_text("Ошибка при отмене. Попробуйте позже.")

    return ConversationHandler.END


def get_my_bookings_handler():
    return MessageHandler(filters.Regex("^📋 Мои записи$"), my_bookings)


def get_cancel_handler():
    return ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^❌ Отменить запись$"), start_cancel)],
        states={
            CANCEL_SELECT: [CallbackQueryHandler(do_cancel, pattern="^cancel_")],
        },
        fallbacks=[],
    )