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
