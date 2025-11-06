from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Генерирует клавиатуру для админ-панели."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="📥 Выгрузить ID пользователей", callback_data="admin_export_users"
        )
    )
    return builder.as_markup()


def get_admin_reply_keyboard(user_count: int = 0) -> ReplyKeyboardMarkup:
    """Генерирует reply клавиатуру для админ-панели."""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="📥 Выгрузить ID пользователей"))
    builder.row(KeyboardButton(text=f"👥 Пользователи ({user_count})"))
    builder.row(KeyboardButton(text="📋 Показать всех подписчиков"))
    return builder.as_markup(resize_keyboard=True)


# For now, an empty file that will contain admin-specific keyboards when needed
