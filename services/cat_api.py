import logging
import aiohttp

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
                    return data[0]["url"]
                else:
                    logger.error(f"Ошибка API TheCatApi: Статус {response.status}")
                    return None
    except Exception as e:
        logger.error(f"Не удалось получить картинку с котом: {e}")
        return None
