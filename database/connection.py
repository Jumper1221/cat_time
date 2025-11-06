import aiosqlite
import logging

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