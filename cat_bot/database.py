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
