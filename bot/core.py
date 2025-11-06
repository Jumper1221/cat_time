from aiogram import Bot
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import Dispatcher
from aiogram.client.default import DefaultBotProperties

from config.settings import BOT_TOKEN, logger


def create_bot() -> Bot:
    """Create and configure the bot instance."""
    if not BOT_TOKEN:
        logger.critical("BOT_TOKEN is not set!")
        raise ValueError("BOT_TOKEN is required")

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    return bot


def create_dispatcher() -> Dispatcher:
    """Create and configure the dispatcher."""
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    return dp
