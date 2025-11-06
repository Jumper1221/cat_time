import logging
from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from database.users import get_users_with_times, remove_user
from services.cat_api import get_cat_image_url

logger = logging.getLogger(__name__)


async def send_daily_cats(bot: Bot, db_path: str, cat_api_key: str):
    """Функция для ежедневной рассылки котов."""
    logger.info("Начало ежедневной рассылки...")
    users_with_times = await get_users_with_times()
    image_url = await get_cat_image_url(cat_api_key)

    if not image_url:
        logger.error("Не удалось получить картинку для рассылки. Рассылка отменена.")
        return

    from datetime import datetime, timezone
    import pytz

    sent_count = 0
    current_utc_hour = datetime.now(timezone.utc).hour

    for user_id, daily_cat_time, user_timezone in users_with_times:
        try:
            # Convert user's local preferred time to UTC for comparison
            user_tz = pytz.timezone(user_timezone)
            now = datetime.now()
            # Create a datetime object with the user's preferred local time today
            local_time_pref = datetime.combine(
                now.date(), datetime.min.time().replace(hour=daily_cat_time)
            )
            # Localize to user's timezone
            local_time_pref = user_tz.localize(local_time_pref)
            # Convert to UTC to see what UTC hour this corresponds to
            utc_time_pref = local_time_pref.astimezone(timezone.utc)
            utc_hour_for_user = utc_time_pref.hour

            # Check if the current UTC hour matches what this user should receive based on their timezone
            if utc_hour_for_user == current_utc_hour:
                try:
                    await bot.send_photo(
                        chat_id=user_id,
                        photo=image_url,
                        caption="Ваш ежедневный котик! 🐾",
                    )
                    sent_count += 1
                except (TelegramForbiddenError, TelegramBadRequest):
                    logger.warning(
                        f"Пользователь {user_id} заблокировал бота или чат не найден. Удаляем из базы."
                    )
                    await remove_user(user_id)
                except Exception as e:
                    logger.error(
                        f"Не удалось отправить сообщение пользователю {user_id}: {e}"
                    )
        except Exception as e:
            logger.error(
                f"Ошибка при обработке пользователя {user_id} в таймзоне {user_timezone}: {e}"
            )

    logger.info(
        f"Рассылка завершена. Отправлено {sent_count} из {len(users_with_times)} возможных сообщений."
    )
