#!/bin/bash

# Название главной папки проекта
PROJECT_DIR="cat_bot"

# Проверка, не существует ли уже такая папка
if [ -d "$PROJECT_DIR" ]; then
    echo "Ошибка: Директория '$PROJECT_DIR' уже существует. Удалите ее или переместите, чтобы продолжить."
    exit 1
fi

echo "Создание структуры проекта в папке '$PROJECT_DIR'..."

# Создаем главную папку и переходим в нее
mkdir "$PROJECT_DIR"
cd "$PROJECT_DIR"

# --- Создание файлов с содержимым ---

# .gitignore
cat << EOF > .gitignore
# Исключения для Python
__pycache__/
*.pyc
*.pyo
*.pyd

# Виртуальное окружение
venv/
.venv/

# Файл с переменными окружения
.env

# Данные и логи
/data/

# Файлы IDE
.idea/
.vscode/
EOF

# requirements.txt
cat << EOF > requirements.txt
aiogram==3.4.1
python-dotenv==1.0.1
aiohttp==3.9.3
aiosqlite==0.20.0
apscheduler==3.10.4
EOF

# .env (шаблон)
cat << EOF > .env
# Токен вашего бота от @BotFather
BOT_TOKEN="ВАШ_ТЕЛЕГРАМ_БОТ_ТОКЕН"

# API ключ от TheCatApi (https://thecatapi.com/signup)
CAT_API_KEY="ВАШ_КЛЮЧ_ОТ_THECATAPI"

# --- Настройки ---
# Путь к базе данных (внутри контейнера)
DATABASE_NAME=./data/users.db

# Путь к файлу логов (внутри контейнера)
LOG_FILE=./data/bot.log

# ID вашего Telegram аккаунта для получения уведомлений (опционально)
ADMIN_ID=""
EOF

# keyboards.py
cat << 'EOF' > keyboards.py
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_main_keyboard(is_subscribed: bool) -> InlineKeyboardMarkup:
    """Генерирует основную клавиатуру в зависимости от статуса подписки."""
    builder = InlineKeyboardBuilder()
    
    if is_subscribed:
        builder.row(
            InlineKeyboardButton(text="❌ Отписаться от рассылки", callback_data="unsubscribe")
        )
    else:
        builder.row(
            InlineKeyboardButton(text="✅ Подписаться на рассылку", callback_data="subscribe")
        )
        
    builder.row(
        InlineKeyboardButton(text="🐱 Получить случайного кота", callback_data="get_cat")
    )
    return builder.as_markup()
EOF

# database.py
cat << 'EOF' > database.py
import aiosqlite
import logging

# Настройка логирования
logger = logging.getLogger(__name__)

async def init_db(database_path: str):
    """Инициализирует базу данных и создает таблицу, если она не существует."""
    async with aiosqlite.connect(database_path) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await db.commit()
    logger.info("База данных успешно инициализирована.")

async def is_user_subscribed(db_path: str, user_id: int) -> bool:
    """Проверяет, подписан ли пользователь."""
    async with aiosqlite.connect(db_path) as db:
        async with db.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,)) as cursor:
            return await cursor.fetchone() is not None

async def add_user(db_path: str, user_id: int):
    """Добавляет пользователя в базу данных (подписывает на рассылку)."""
    async with aiosqlite.connect(db_path) as db:
        try:
            await db.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
            await db.commit()
            logger.info(f"Пользователь {user_id} подписался на рассылку.")
        except aiosqlite.IntegrityError:
            logger.warning(f"Попытка повторной подписки пользователя {user_id}.")

async def remove_user(db_path: str, user_id: int):
    """Удаляет пользователя из базы данных (отписывает от рассылки)."""
    async with aiosqlite.connect(db_path) as db:
        await db.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        await db.commit()
        logger.info(f"Пользователь {user_id} отписался от рассылки.")

async def get_all_users(db_path: str) -> list[int]:
    """Возвращает список ID всех подписанных пользователей."""
    async with aiosqlite.connect(db_path) as db:
        async with db.execute("SELECT user_id FROM users") as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]
EOF

# scheduler.py
cat << 'EOF' > scheduler.py
import logging
import aiohttp
from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from database import get_all_users, remove_user

logger = logging.getLogger(__name__)

async def get_cat_image_url(api_key: str) -> str | None:
    """Получает URL случайной картинки с котом."""
    url = "https://api.thecatapi.com/v1/images/search"
    headers = {"x-api-key": api_key}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data[0]['url']
                else:
                    logger.error(f"Ошибка API TheCatApi: Статус {response.status}")
                    return None
    except Exception as e:
        logger.error(f"Не удалось получить картинку с котом: {e}")
        return None

async def send_daily_cats(bot: Bot, db_path: str, cat_api_key: str):
    """Функция для ежедневной рассылки котов."""
    logger.info("Начало ежедневной рассылки...")
    users = await get_all_users(db_path)
    image_url = await get_cat_image_url(cat_api_key)

    if not image_url:
        logger.error("Не удалось получить картинку для рассылки. Рассылка отменена.")
        return

    sent_count = 0
    for user_id in users:
        try:
            await bot.send_photo(
                chat_id=user_id,
                photo=image_url,
                caption="Ваш ежедневный котик! 🐾"
            )
            sent_count += 1
        except (TelegramForbiddenError, TelegramBadRequest) as e:
            logger.warning(f"Пользователь {user_id} заблокировал бота или чат не найден. Удаляем из базы.")
            await remove_user(db_path, user_id)
        except Exception as e:
            logger.error(f"Не удалось отправить сообщение пользователю {user_id}: {e}")
            
    logger.info(f"Рассылка завершена. Отправлено {sent_count} из {len(users)} сообщений.")
EOF

# handlers.py
cat << 'EOF' > handlers.py
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart

import database as db
import keyboards as kb
from scheduler import get_cat_image_url

router = Router()
logger = logging.getLogger(__name__)

# Хэндлер на команду /start
@router.message(CommandStart())
async def cmd_start(message: Message, db_path: str):
    user_id = message.from_user.id
    is_subscribed = await db.is_user_subscribed(db_path, user_id)
    
    await message.answer(
        "Привет! Я бот, который будет присылать тебе котиков 😺",
        reply_markup=kb.get_main_keyboard(is_subscribed)
    )

# Хэндлер для колбэка "Подписаться"
@router.callback_query(F.data == "subscribe")
async def cb_subscribe(callback: CallbackQuery, db_path: str):
    user_id = callback.from_user.id
    await db.add_user(db_path, user_id)
    await callback.answer("Вы успешно подписались на рассылку! 🎉", show_alert=True)
    await callback.message.edit_reply_markup(reply_markup=kb.get_main_keyboard(is_subscribed=True))

# Хэндлер для колбэка "Отписаться"
@router.callback_query(F.data == "unsubscribe")
async def cb_unsubscribe(callback: CallbackQuery, db_path: str):
    user_id = callback.from_user.id
    await db.remove_user(db_path, user_id)
    await callback.answer("Вы отписались от рассылки. 😿", show_alert=True)
    await callback.message.edit_reply_markup(reply_markup=kb.get_main_keyboard(is_subscribed=False))

# Хэндлер для колбэка "Получить кота"
@router.callback_query(F.data == "get_cat")
async def cb_get_cat(callback: CallbackQuery, cat_api_key: str):
    await callback.answer("Ищу котика...", show_alert=False)
    image_url = await get_cat_image_url(cat_api_key)
    if image_url:
        try:
            await callback.message.answer_photo(
                photo=image_url,
                caption="Вот ваш случайный котик! ❤️"
            )
        except Exception as e:
            logger.error(f"Ошибка отправки фото: {e}")
            await callback.message.answer("Ой, не удалось загрузить котика. Попробуйте еще раз.")
    else:
        await callback.message.answer("Что-то пошло не так, котик убежал. Попробуйте позже.")
EOF

# bot.py
cat << 'EOF' > bot.py
import asyncio
import logging
import os
from logging.handlers import RotatingFileHandler

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import database as db
from handlers import router
from scheduler import send_daily_cats

# Загружаем переменные окружения в самом начале
load_dotenv()

# Настройка логирования
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log_file = os.getenv('LOG_FILE', 'data/bot.log')

# Создаем папку для логов, если ее нет
os.makedirs(os.path.dirname(log_file), exist_ok=True)

# Логгер для файла с ротацией
file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=2, encoding='utf-8')
file_handler.setFormatter(log_formatter)

# Логгер для вывода в консоль
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)

logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, console_handler]
)
logger = logging.getLogger(__name__)

# Читаем переменные окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
CAT_API_KEY = os.getenv("CAT_API_KEY")
DATABASE_NAME = os.getenv("DATABASE_NAME")
ADMIN_ID = os.getenv("ADMIN_ID")


async def main():
    if not BOT_TOKEN or not CAT_API_KEY or not DATABASE_NAME:
        logger.critical("Необходимые переменные окружения не установлены! (BOT_TOKEN, CAT_API_KEY, DATABASE_NAME)")
        return

    # Инициализация базы данных
    await db.init_db(DATABASE_NAME)
    
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Передаем пути и ключи в хэндлеры через middleware
    dp['db_path'] = DATABASE_NAME
    dp['cat_api_key'] = CAT_API_KEY
    
    # Подключаем роутер
    dp.include_router(router)
    
    # Настройка и запуск планировщика
    # Важно: Укажите ваш часовой пояс! Например, "Europe/Moscow", "Asia/Yekaterinburg"
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    scheduler.add_job(
        send_daily_cats,
        'cron',
        hour=9,
        minute=0,
        args=(bot, DATABASE_NAME, CAT_API_KEY)
    )
    scheduler.start()
    
    logger.info("Бот запускается...")
    if ADMIN_ID:
        try:
            await bot.send_message(ADMIN_ID, "Бот успешно запущен!")
        except Exception as e:
            logger.warning(f"Не удалось отправить сообщение администратору ({ADMIN_ID}): {e}")

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
EOF

# Dockerfile
cat << 'EOF' > Dockerfile
# Используем официальный образ Python
FROM python:3.10-slim

# Устанавливаем рабочую директорию в контейнере
WORKDIR /app

# Копируем файл с зависимостями
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код приложения в рабочую директорию
COPY . .

# Указываем команду для запуска бота при старте контейнера
CMD ["python", "bot.py"]
EOF

# --- Завершение ---
echo ""
echo "✅ Структура проекта '$PROJECT_DIR' успешно создана!"
echo ""
echo "--- Следующие шаги: ---"
echo "1. Перейдите в папку проекта:"
echo "   cd $PROJECT_DIR"
echo ""
echo "2. Отредактируйте файл .env и вставьте ваши реальные токены:"
echo "   nano .env"
echo ""
echo "3. Соберите Docker-образ:"
echo "   docker build -t cat-bot-image ."
echo ""
echo "4. Запустите Docker-контейнер:"
echo "   docker run -d --name cat-bot-container --restart always --env-file ./.env cat-bot-image"
echo ""
echo "Для просмотра логов используйте:"
echo "   docker logs -f cat-bot-container"
echo ""