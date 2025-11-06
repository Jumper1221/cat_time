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


async def add_user(
    user_id: int, daily_cat_time: int = 9, timezone: str = "Europe/Moscow"
):
    """Добавляет пользователя в базу данных (подписывает на рассылку)."""
    db_conn = get_db_connection()
    if not db_conn:
        logger.error("Database connection not initialized")
        return

    try:
        await db_conn.execute_command(
            "INSERT INTO users (user_id, daily_cat_time, timezone) VALUES (?, ?, ?)",
            (user_id, daily_cat_time, timezone),
        )
        logger.info(
            f"Пользователь {user_id} подписался на рассылку с временем {daily_cat_time}:00 (по {timezone})."
        )
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


async def get_users_with_times() -> List[tuple]:
    """Возвращает список кортежей (user_id, daily_cat_time, timezone) для всех подписанных пользователей."""
    db_conn = get_db_connection()
    if not db_conn:
        logger.error("Database connection not initialized")
        return []

    try:
        rows = await db_conn.execute_query(
            "SELECT user_id, daily_cat_time, timezone FROM users"
        )
        return [(row[0], row[1], row[2]) for row in rows]
    except Exception as e:
        logger.error(f"Error getting users with times: {e}")
        return []


async def update_user_time(user_id: int, daily_cat_time: int):
    """Обновляет время получения ежедневного кота для пользователя."""
    db_conn = get_db_connection()
    if not db_conn:
        logger.error("Database connection not initialized")
        return

    try:
        await db_conn.execute_command(
            "UPDATE users SET daily_cat_time = ? WHERE user_id = ?",
            (daily_cat_time, user_id),
        )
        logger.info(
            f"Время получения кота для пользователя {user_id} обновлено на {daily_cat_time}:00 (по UTC)."
        )
    except Exception as e:
        logger.error(f"Error updating user time: {e}")


async def get_user_timezone(user_id: int) -> str:
    """Получает таймзону пользователя из базы данных."""
    db_conn = get_db_connection()
    if not db_conn:
        logger.error("Database connection not initialized")
        return "Europe/Moscow" # Default timezone

    try:
        rows = await db_conn.execute_query(
            "SELECT timezone FROM users WHERE user_id = ?", (user_id,)
        )
        if rows:
            return rows[0][0]  # Return the timezone from the first row
        else:
            return "Europe/Moscow"  # Default timezone if user not found
    except Exception as e:
        logger.error(f"Error getting user timezone: {e}")
        return "Europe/Moscow"  # Default timezone on error


async def update_user_timezone(user_id: int, timezone: str):
    """Обновляет таймзону пользователя в базе данных."""
    db_conn = get_db_connection()
    if not db_conn:
        logger.error("Database connection not initialized")
        return

    try:
        await db_conn.execute_command(
            "UPDATE users SET timezone = ? WHERE user_id = ?",
            (timezone, user_id),
        )
        logger.info(
            f"Timezone for user {user_id} updated to {timezone}."
        )
    except Exception as e:
        logger.error(f"Error updating user timezone: {e}")
