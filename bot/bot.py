import os
import logging
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder
from bot.handlers.start import get_start_handler
from bot.handlers.booking import get_booking_handler
from bot.handlers.my_bookings import get_my_bookings_handler, get_cancel_handler

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Настройка логирования — пишет и в терминал и в файл
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),                          # в терминал
        logging.FileHandler("bot.log", encoding="utf-8") # в файл bot.log
    ]
)
logger = logging.getLogger(__name__)


def main():
    logger.info("Запуск бота...")
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(get_start_handler())
    app.add_handler(get_booking_handler())
    app.add_handler(get_my_bookings_handler())
    app.add_handler(get_cancel_handler())

    logger.info("Бот запущен, начинаем polling")
    app.run_polling()


if __name__ == "__main__":
    main()