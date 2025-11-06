from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def get_admin_keyboard(user_count: int = 0, bot_user_count: int = 0) -> InlineKeyboardMarkup:
    """Генерирует клавиатуру для админ-панели."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=f"Количество подписчиков ({user_count})", callback_data="admin_show_subscribers"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=f"Всего пользователей ({bot_user_count})", callback_data="admin_show_all_users"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Выгрузить данные", callback_data="admin_export_data"
        )
    )
    return builder.as_markup()


def get_admin_reply_keyboard(
    user_count: int = 0, bot_user_count: int = 0
) -> ReplyKeyboardMarkup:
    """Генерирует reply клавиатуру для админ-панели."""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text=f"Количество подписчиков ({user_count})"))
    builder.row(KeyboardButton(text=f"Всего пользователей ({bot_user_count})"))
    builder.row(KeyboardButton(text="Выгрузить данные"))
    return builder.as_markup(resize_keyboard=True)
