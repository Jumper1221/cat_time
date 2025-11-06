import logging
from typing import List
from database.connection import get_db_connection
from database.models import User

logger = logging.getLogger(__name__)


async def is_user_subscribed(user_id: int) -> bool:
    """Проверяет, подписан ли пользователь."""
    db_conn = get_db_connection()
    if not db_conn:
        logger.error("Database connection not initialized")
        return False

    try:
        rows = await db_conn.execute_query(
            "SELECT 1 FROM users WHERE user_id = ?", (user_id,)
        )
        return len(rows) > 0
    except Exception as e:
        logger.error(f"Error checking if user is subscribed: {e}")
        return False


async def add_user(user_id: int):
    """Добавляет пользователя в базу данных (подписывает на рассылку)."""
    db_conn = get_db_connection()
    if not db_conn:
        logger.error("Database connection not initialized")
        return

    try:
        await db_conn.execute_command(
            "INSERT INTO users (user_id) VALUES (?)", (user_id,)
        )
        logger.info(f"Пользователь {user_id} подписался на рассылку.")
    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            logger.warning(f"Попытка повторной подписки пользователя {user_id}.")
        else:
            logger.error(f"Error adding user: {e}")


async def remove_user(user_id: int):
    """Удаляет пользователя из базы данных (отписывает от рассылки)."""
    db_conn = get_db_connection()
    if not db_conn:
        logger.error("Database connection not initialized")
        return

    try:
        await db_conn.execute_command("DELETE FROM users WHERE user_id = ?", (user_id,))
        logger.info(f"Пользователь {user_id} отписался от рассылки.")
    except Exception as e:
        logger.error(f"Error removing user: {e}")


async def get_all_users() -> List[int]:
    """Возвращает список ID всех подписанных пользователей."""
    db_conn = get_db_connection()
    if not db_conn:
        logger.error("Database connection not initialized")
        return []

    try:
        rows = await db_conn.execute_query("SELECT user_id FROM users")
        return [row[0] for row in rows]
    except Exception as e:
        logger.error(f"Error getting all users: {e}")
        return []
