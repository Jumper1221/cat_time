from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_main_keyboard(is_subscribed: bool) -> InlineKeyboardMarkup:
    """Генерирует основную клавиатуру в зависимости от статуса подписки."""
    builder = InlineKeyboardBuilder()

    if is_subscribed:
        builder.row(
            InlineKeyboardButton(
                text="❌ Отписаться от рассылки", callback_data="unsubscribe"
            )
        )
    else:
        builder.row(
            InlineKeyboardButton(
                text="✅ Подписаться на рассылку", callback_data="subscribe"
            )
        )

    builder.row(
        InlineKeyboardButton(
            text="🐱 Получить случайного кота", callback_data="get_cat"
        )
    )
    return builder.as_markup()
