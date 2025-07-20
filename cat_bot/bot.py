import asyncio
import logging
import os
from logging.handlers import RotatingFileHandler

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import database as db
from handlers import router as main_router, admin_router  # 1. Импортируем оба роутера
from scheduler import send_daily_cats
from filters import IsAdmin  # 2. Импортируем фильтр

# Загружаем переменные окружения в самом начале
load_dotenv()

# Настройка логирования
log_formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
log_file = os.getenv("LOG_FILE", "data/bot.log")

# Создаем папку для логов, если ее нет
os.makedirs(os.path.dirname(log_file), exist_ok=True)

# Логгер для файла с ротацией
file_handler = RotatingFileHandler(
    log_file, maxBytes=5 * 1024 * 1024, backupCount=2, encoding="utf-8"
)
file_handler.setFormatter(log_formatter)

# Логгер для вывода в консоль
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)

logging.basicConfig(level=logging.INFO, handlers=[file_handler, console_handler])
logger = logging.getLogger(__name__)

# Читаем переменные окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
CAT_API_KEY = os.getenv("CAT_API_KEY")
DATABASE_NAME = os.getenv("DATABASE_NAME")
ADMIN_ID = os.getenv("ADMIN_ID")


async def main():
    if not BOT_TOKEN or not CAT_API_KEY or not DATABASE_NAME:
        logger.critical(
            "Необходимые переменные окружения не установлены! (BOT_TOKEN, CAT_API_KEY, DATABASE_NAME)"
        )
        return

    # 3. Обрабатываем ADMIN_ID и создаем список для фильтра
    if not ADMIN_ID:
        logger.warning(
            "Переменная ADMIN_ID не установлена. Админ-функции будут недоступны."
        )
        admin_ids = []
    else:
        try:
            admin_ids = [int(ADMIN_ID)]
        except ValueError:
            logger.error(
                "ADMIN_ID имеет неверный формат. Это должно быть число. Админ-функции отключены."
            )
            admin_ids = []

    # Инициализация базы данных
    await db.init_db(DATABASE_NAME)

    bot = Bot(token=BOT_TOKEN, parse_mode="HTML")  # Добавим parse_mode по умолчанию
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Передаем пути и ключи в хэндлеры через middleware
    dp["db_path"] = DATABASE_NAME
    dp["cat_api_key"] = CAT_API_KEY

    # 4. Регистрируем роутеры
    dp.include_router(main_router)

    # Применяем фильтр IsAdmin ко всем хендлерам в admin_router
    admin_router.message.filter(IsAdmin(admin_ids))
    admin_router.callback_query.filter(IsAdmin(admin_ids))
    dp.include_router(admin_router)

    # Настройка и запуск планировщика
    # Важно: Укажите ваш часовой пояс! Например, "Europe/Moscow", "Asia/Yekaterinburg"
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    scheduler.add_job(
        send_daily_cats,
        "cron",
        hour=9,
        minute=0,
        args=(bot, DATABASE_NAME, CAT_API_KEY),
    )
    scheduler.start()

    logger.info("Бот запускается...")
    if admin_ids:
        try:
            await bot.send_message(admin_ids[0], "Бот успешно запущен!")
        except Exception as e:
            logger.warning(
                f"Не удалось отправить сообщение администратору ({admin_ids[0]}): {e}"
            )

    # Запускаем бота
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен.")
    except Exception as e:
        logger.critical(f"Критическая ошибка при запуске бота: {e}", exc_info=True)
