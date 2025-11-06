import aiosqlite
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Centralized database connection manager for the application."""

    def __init__(self, database_path: str):
        self.database_path = database_path

    @asynccontextmanager
    async def get_db(self) -> AsyncGenerator[aiosqlite.Connection, None]:
        """Provides a database connection context."""
        async with aiosqlite.connect(self.database_path) as db:
            yield db

    async def init_db(self):
        """Инициализирует базу данных и создает таблицы, если они не существуют."""
        async with self.get_db() as db:
            # Таблица для подписчиков
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Таблица для всех пользователей, которые использовали бота
            await db.execute("""
                CREATE TABLE IF NOT EXISTS bot_users (
                    user_id INTEGER PRIMARY KEY,
                    first_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.commit()
        logger.info("База данных успешно инициализирована.")

    async def execute_query(self, query: str, params: tuple = ()) -> list:
        """Execute a SELECT query and return results."""
        async with self.get_db() as db:
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return list(rows)

    async def execute_command(self, query: str, params: tuple = ()) -> None:
        """Execute an INSERT/UPDATE/DELETE command."""
        async with self.get_db() as db:
            await db.execute(query, params)
            await db.commit()


# Global database instance
_db_instance = None


def get_db_connection() -> DatabaseConnection | None:
    """Get the global database connection instance."""
    global _db_instance
    return _db_instance


def init_db_connection(database_path: str) -> DatabaseConnection:
    """Initialize the global database connection instance."""
    global _db_instance
    _db_instance = DatabaseConnection(database_path)
    return _db_instance
