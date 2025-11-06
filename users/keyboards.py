from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_main_keyboard(is_subscribed: bool) -> InlineKeyboardMarkup:
    """Генерирует основную клавиатуру в зависимости от статуса подписки."""
    builder = InlineKeyboardBuilder()

    if not is_subscribed:
        builder.row(
            InlineKeyboardButton(
                text="✅ Подписаться на рассылку", callback_data="subscribe"
            )
        )

    builder.row(InlineKeyboardButton(text="⚙️ Настройки", callback_data="show_settings"))

    builder.row(
        InlineKeyboardButton(
            text="🐱 Получить случайного кота", callback_data="get_cat"
        )
    )
    return builder.as_markup()


def get_time_selection_keyboard() -> InlineKeyboardMarkup:
    """Генерирует клавиатуру для выбора времени получения кота."""
    builder = InlineKeyboardBuilder()

    # Create buttons for each hour of the day (00:00 to 23:00)
    for hour in range(24):
        time_text = f"{hour:02d}:00"
        callback_data = f"set_time_{hour:02d}"
        builder.button(text=time_text, callback_data=callback_data)

    # Add a back button
    builder.button(text="◀️ Назад", callback_data="back_to_main")

    builder.adjust(4)  # 4 buttons per row
    return builder.as_markup()


def get_timezone_change_keyboard() -> InlineKeyboardMarkup:
    """Генерирует клавиатуру для изменения таймзоны."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="📍 Определить по местоположению", callback_data="request_location"
    )
    builder.button(text="🕐 Выбрать из списка", callback_data="select_timezone")
    builder.button(text="◀️ Назад", callback_data="back_to_main")
    builder.adjust(1)  # Arrange buttons in a single column
    return builder.as_markup()


def get_main_keyboard_with_timezone(is_subscribed: bool) -> InlineKeyboardMarkup:
    """Генерирует основную клавиатуру с опцией изменения таймзоны."""
    builder = InlineKeyboardBuilder()

    if not is_subscribed:
        builder.row(
            InlineKeyboardButton(
                text="✅ Подписаться на рассылку", callback_data="subscribe"
            )
        )

    builder.row(InlineKeyboardButton(text="⚙️ Настройки", callback_data="show_settings"))

    builder.row(
        InlineKeyboardButton(
            text="🐱 Получить случайного кота", callback_data="get_cat"
        )
    )
    return builder.as_markup()


def get_timezone_selection_keyboard() -> InlineKeyboardMarkup:
    """Генерирует клавиатуру для выбора таймзоны по UTC сдвигу."""
    builder = InlineKeyboardBuilder()

    # Add common UTC offsets
    utc_offsets = [
        ("UTC-12", "Etc/GMT+12"),
        ("UTC-11", "Etc/GMT+11"),
        ("UTC-10", "Etc/GMT+10"),
        ("UTC-9", "Etc/GMT+9"),
        ("UTC-8", "Etc/GMT+8"),
        ("UTC-7", "Etc/GMT+7"),
        ("UTC-6", "Etc/GMT+6"),
        ("UTC-5", "Etc/GMT+5"),
        ("UTC-4", "Etc/GMT+4"),
        ("UTC-3", "Etc/GMT+3"),
        ("UTC-2", "Etc/GMT+2"),
        ("UTC-1", "Etc/GMT+1"),
        ("UTC+0", "Etc/GMT+0"),
        ("UTC+1", "Etc/GMT-1"),
        ("UTC+2", "Etc/GMT-2"),
        ("UTC+3", "Europe/Moscow"),
        ("UTC+4", "Europe/Samara"),
        ("UTC+5", "Asia/Yekaterinburg"),
        ("UTC+6", "Asia/Almaty"),
        ("UTC+7", "Asia/Bangkok"),
        ("UTC+8", "Asia/Shanghai"),
        ("UTC+9", "Asia/Tokyo"),
        ("UTC+10", "Australia/Brisbane"),
        ("UTC+11", "Australia/Sydney"),
        ("UTC+12", "Pacific/Fiji"),
    ]

    for utc_text, tz_value in utc_offsets:
        builder.button(text=utc_text, callback_data=f"tz_{tz_value}")

    builder.button(text="◀️ Назад", callback_data="back_to_main")
    builder.adjust(3)  # 3 buttons per row
    return builder.as_markup()


def get_settings_keyboard(is_subscribed: bool = False) -> InlineKeyboardMarkup:
    """Генерирует клавиатуру для настроек."""
    builder = InlineKeyboardBuilder()

    if is_subscribed:
        builder.button(text="❌ Отписаться от рассылки", callback_data="unsubscribe")

    builder.button(text="🕐 Изменить время получения кота", callback_data="change_time")
    builder.button(text="🌍 Изменить таймзону", callback_data="change_timezone")
    builder.button(text="◀️ Назад", callback_data="back_to_main")
    builder.adjust(1)  # Arrange buttons in a single column
    return builder.as_markup()
