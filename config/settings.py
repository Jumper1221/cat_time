import os
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
CAT_API_KEY = os.getenv("CAT_API_KEY")
DATABASE_NAME = os.getenv("DATABASE_NAME")
ADMIN_ID = os.getenv("ADMIN_ID")

# Logging configuration
log_formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
log_file = os.getenv("LOG_FILE", "data/bot.log")

# Create log directory if it doesn't exist
os.makedirs(os.path.dirname(log_file), exist_ok=True)

# File handler with rotation
file_handler = RotatingFileHandler(
    log_file, maxBytes=5 * 1024 * 1024, backupCount=2, encoding="utf-8"
)
file_handler.setFormatter(log_formatter)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)

# Configure logging
logging.basicConfig(level=logging.INFO, handlers=[file_handler, console_handler])
logger = logging.getLogger(__name__)

# Admin IDs list
def get_admin_ids():
    if not ADMIN_ID:
        logger.warning(
            "Переменная ADMIN_ID не установлена. Админ-функции будут недоступны."
        )
        return []
    try:
        return [int(ADMIN_ID)]
    except ValueError:
        logger.error(
            "ADMIN_ID имеет неверный формат. Это должно быть число. Админ-функции отключены."
        )
        return []