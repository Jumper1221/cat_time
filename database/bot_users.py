import logging
from typing import List
from database.connection import get_db_connection
from database.models import BotUser

logger = logging.getLogger(__name__)


async def is_bot_user(user_id: int) -> bool:
    """Проверяет, использовал ли пользователь бота ранее."""
    db_conn = get_db_connection()
    if not db_conn:
        logger.error("Database connection not initialized")
        return False
        
    try:
        rows = await db_conn.execute_query(
            "SELECT 1 FROM bot_users WHERE user_id = ?", (user_id,)
        )
        return len(rows) > 0
    except Exception as e:
        logger.error(f"Error checking if user is bot user: {e}")
        return False


async def add_bot_user(user_id: int):
    """Добавляет пользователя в таблицу bot_users при первом использовании."""
    db_conn = get_db_connection()
    if not db_conn:
        logger.error("Database connection not initialized")
        return
        
    try:
        await db_conn.execute_command(
            "INSERT INTO bot_users (user_id) VALUES (?)", (user_id,)
        )
        logger.info(f"Пользователь {user_id} добавлен в таблицу bot_users.")
    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            logger.warning(
                f"Пользователь {user_id} уже существует в таблице bot_users."
            )
        else:
            logger.error(f"Error adding bot user: {e}")


async def get_all_bot_users() -> List[int]:
    """Возвращает список ID всех пользователей, которые использовали бота."""
    db_conn = get_db_connection()
    if not db_conn:
        logger.error("Database connection not initialized")
        return []
        
    try:
        rows = await db_conn.execute_query("SELECT user_id FROM bot_users")
        return [row[0] for row in rows]
    except Exception as e:
        logger.error(f"Error getting all bot users: {e}")
        return []


async def get_non_subscribed_bot_users() -> List[int]:
    """Возвращает список ID пользователей, которые использовали бота но не подписаны."""
    db_conn = get_db_connection()
    if not db_conn:
        logger.error("Database connection not initialized")
        return []
        
    try:
        # Получаем пользователей, которые есть в bot_users, но нет в users (не подписаны)
        rows = await db_conn.execute_query("""
            SELECT bu.user_id
            FROM bot_users bu
            LEFT JOIN users u ON bu.user_id = u.user_id
            WHERE u.user_id IS NULL
        """)
        return [row[0] for row in rows]
    except Exception as e:
        logger.error(f"Error getting non-subscribed bot users: {e}")
        return []


async def get_first_used_at(user_id: int) -> str | None:
    """Возвращает дату и время первого использования бота пользователем."""
    db_conn = get_db_connection()
    if not db_conn:
        logger.error("Database connection not initialized")
        return None
        
    try:
        rows = await db_conn.execute_query(
            "SELECT first_used_at FROM bot_users WHERE user_id = ?", (user_id,)
        )
        return rows[0][0] if rows else None
    except Exception as e:
        logger.error(f"Error getting first used at: {e}")
        return None
