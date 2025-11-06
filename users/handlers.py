import logging
from typing import Optional
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InaccessibleMessage
from aiogram.filters import CommandStart, Command
from aiogram.exceptions import TelegramBadRequest

from database.users import (
    is_user_subscribed,
    add_user,
    remove_user,
    get_all_users,
    update_user_time,
    update_user_timezone,
    get_user_timezone,
)
from database.bot_users import is_bot_user, add_bot_user
import users.keyboards as kb
from services.cat_api import get_cat_image_url

# Main router for users
router = Router()
logger = logging.getLogger(__name__)

# ==================== UTILITY FUNCTIONS ====================


async def safe_edit_message_or_answer(
    callback: CallbackQuery, text: str, reply_markup=None
) -> None:
    """Safely edit a message or send a new one if editing is not possible."""
    if callback.message is None:
        await callback.answer("Ошибка: невозможно получить сообщение.", show_alert=True)
        return

    if isinstance(callback.message, InaccessibleMessage):
        # If message is inaccessible, answer to the callback instead
        await callback.answer(text, show_alert=True)
        return

    try:
        await callback.message.edit_text(text, reply_markup=reply_markup)
    except TelegramBadRequest:
        # If message can't be edited, answer to the callback instead
        await callback.answer(text, show_alert=True)


async def safe_edit_reply_markup_or_answer(
    callback: CallbackQuery, reply_markup=None, text: Optional[str] = None
) -> None:
    """Safely edit reply markup or send a new message if editing is not possible."""
    if callback.message is None:
        await callback.answer("Ошибка: невозможно получить сообщение.", show_alert=True)
        return

    if isinstance(callback.message, InaccessibleMessage):
        # If message is inaccessible, answer to the callback instead
        if text is not None:
            await callback.answer(text, show_alert=True)
        else:
            await callback.answer("Клавиатура обновлена.", show_alert=True)
        return

    try:
        await callback.message.edit_reply_markup(reply_markup=reply_markup)
    except TelegramBadRequest:
        # If reply markup can't be edited, answer to the callback instead
        if text is not None:
            await callback.answer(text, show_alert=True)
        else:
            await callback.answer("Клавиатура обновлена.", show_alert=True)


async def safe_message_answer(
    callback: CallbackQuery, text: str, reply_markup=None
) -> None:
    """Safely answer to a callback query by sending a message."""
    if callback.message is None:
        await callback.answer("Ошибка: невозможно получить сообщение.", show_alert=True)
        return

    if isinstance(callback.message, InaccessibleMessage):
        # If message is inaccessible, answer to the callback instead
        await callback.answer(text, show_alert=True)
        return

    try:
        await callback.message.answer(text, reply_markup=reply_markup)
    except TelegramBadRequest:
        # If message can't be answered to, answer to the callback
        await callback.answer(text, show_alert=True)


async def safe_message_answer_photo(
    callback: CallbackQuery, photo, caption: Optional[str] = None
) -> None:
    """Safely send a photo in response to a callback query."""
    if callback.message is None:
        await callback.answer("Ошибка: невозможно получить сообщение.", show_alert=True)
        return

    if isinstance(callback.message, InaccessibleMessage):
        # If message is inaccessible, answer to the callback instead
        answer_text = caption if caption is not None else "Отправка фото не удалась."
        await callback.answer(answer_text, show_alert=True)
        return

    try:
        await callback.message.answer_photo(photo=photo, caption=caption)
    except TelegramBadRequest:
        # If photo can't be sent to the original message, answer to callback
        answer_text = caption if caption is not None else "Отправка фото не удалась."
        await callback.answer(answer_text, show_alert=True)


@router.message(CommandStart())
async def cmd_start(message: Message, db_path: str):
    if message.from_user is None:
        return  # Can't proceed without user info
    user_id = message.from_user.id

    # Register user if first interaction
    if not await is_bot_user(user_id):
        await add_bot_user(user_id)

    is_subscribed = await is_user_subscribed(user_id)

    # Always show the main inline keyboard to all users
    inline_keyboard = kb.get_main_keyboard(is_subscribed)
    await message.answer(
        "Привет! Я бот, который будет присылать тебе котиков 😺",
        reply_markup=inline_keyboard,
    )

    # For admin users, also send the reply keyboard to show at the bottom of the app
    try:
        from admin.keyboards import get_admin_reply_keyboard
        from config.settings import get_admin_ids

        admin_ids = get_admin_ids()
        if user_id in admin_ids:
            # Get user count for admin keyboard
            users = await get_all_users()
            user_count = len(users)
            reply_keyboard = get_admin_reply_keyboard(user_count)
            await message.answer(
                "Вы админ бота. Вот клавиатура для административных функций:",
                reply_markup=reply_keyboard,
            )
    except ImportError:
        pass


@router.message(Command("settings"))
async def cmd_settings(message: Message, db_path: str):
    if message.from_user is None:
        return  # Can't proceed without user info
    user_id = message.from_user.id

    # Register user if first interaction
    if not await is_bot_user(user_id):
        await add_bot_user(user_id)

    # Check subscription status
    is_subscribed = await is_user_subscribed(user_id)

    # Show the settings keyboard
    settings_keyboard = kb.get_settings_keyboard(is_subscribed)
    await message.answer("⚙️ Настройки бота:", reply_markup=settings_keyboard)


@router.message(Command("cat"))
async def cmd_cat(message: Message, cat_api_key: str, db_path: str):
    if message.from_user is None:
        await message.answer("Не удалось получить информацию о пользователе.")
        return

    user_id = message.from_user.id

    # Register user if first interaction
    if not await is_bot_user(user_id):
        await add_bot_user(user_id)

    await message.answer("Ищу котика...", show_alert=False)
    image_url = await get_cat_image_url(cat_api_key)

    if image_url:
        try:
            # Send the cat photo
            await message.answer_photo(
                photo=image_url, caption="Вот ваш случайный котик! ❤️"
            )

            # Send the main menu again
            is_subscribed = await is_user_subscribed(user_id)
            keyboard = kb.get_main_keyboard(is_subscribed)

            try:
                await message.answer("Что делаем дальше?", reply_markup=keyboard)
            except Exception as e:
                logger.error(f"Ошибка отправки сообщения: {e}")

        except Exception as e:
            logger.error(f"Ошибка отправки фото: {e}")
            try:
                await message.answer(
                    "Ой, не удалось загрузить котика. Попробуйте еще раз."
                )
            except Exception as e:
                logger.error(f"Ошибка отправки сообщения: {e}")
    else:
        try:
            await message.answer("Что-то пошло не так, котик убежал. Попробуйте позже.")
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения: {e}")


# ==================== SUBSCRIPTION HANDLERS ====================


@router.callback_query(F.data == "subscribe")
async def cb_subscribe(callback: CallbackQuery, db_path: str):
    user_id = callback.from_user.id

    # Register user if first interaction
    if not await is_bot_user(user_id):
        await add_bot_user(user_id)

    # For new subscriptions, we'll ask for time selection
    time_keyboard = kb.get_time_selection_keyboard()
    await safe_edit_message_or_answer(
        callback,
        "Выберите время, в котором вы хотите получать ежедневного кота:",
        reply_markup=time_keyboard,
    )
    await callback.answer()


@router.callback_query(F.data == "unsubscribe")
async def cb_unsubscribe(callback: CallbackQuery, db_path: str):
    user_id = callback.from_user.id

    # Register user if first interaction
    if not await is_bot_user(user_id):
        await add_bot_user(user_id)

    await remove_user(user_id)
    await callback.answer("Вы отписались от рассылки. 😿", show_alert=True)

    # Show the updated inline keyboard
    keyboard = kb.get_main_keyboard(is_subscribed=False)
    await safe_edit_reply_markup_or_answer(
        callback, keyboard, "Вы отписались от рассылки. Вот клавиатура для управления:"
    )


@router.callback_query(F.data.startswith("set_time_"))
async def cb_set_time(callback: CallbackQuery):
    user_id = callback.from_user.id
    if callback.data is None:
        await callback.answer("Ошибка: нет данных в callback.", show_alert=True)
        return
    hour = int(
        callback.data.split("_")[2]
    )  # Extract hour from callback data like "set_time_09"

    # Get the user's timezone
    user_timezone = await get_user_timezone(user_id)
    if not user_timezone:
        user_timezone = "Europe/Moscow"  # Default timezone

    # Check if user is already subscribed
    if await is_user_subscribed(user_id):
        # Update existing subscription with new time
        await update_user_time(user_id, hour)
        await callback.answer(
            f"Время получения кота изменено на {hour:02d}:00 (по вашему времени {user_timezone})!",
            show_alert=True,
        )
    else:
        # Create new subscription with selected time
        await add_user(user_id, hour, user_timezone)  # Use user's timezone
        await callback.answer(
            f"Вы успешно подписались на рассылку с временем {hour:02d}:00 (по вашему времени {user_timezone})! 🎉",
            show_alert=True,
        )

    # Show the updated inline keyboard
    keyboard = kb.get_main_keyboard(is_subscribed=True)
    await safe_edit_reply_markup_or_answer(
        callback, keyboard, "Вот клавиатура для управления подпиской:"
    )


@router.callback_query(F.data == "change_time")
async def cb_change_time(callback: CallbackQuery):
    # Show time selection keyboard
    time_keyboard = kb.get_time_selection_keyboard()
    await safe_edit_message_or_answer(
        callback,
        "Выберите новое время для получения ежедневного кота:",
        reply_markup=time_keyboard,
    )
    await callback.answer()


# ==================== NAVIGATION HANDLERS ====================


@router.callback_query(F.data == "back_to_main")
async def cb_back_to_main(callback: CallbackQuery):
    # Show the main keyboard
    is_subscribed = await is_user_subscribed(callback.from_user.id)
    keyboard = kb.get_main_keyboard(is_subscribed)
    await safe_edit_reply_markup_or_answer(
        callback, keyboard, "Вот клавиатура для управления подпиской:"
    )
    await callback.answer()


@router.callback_query(F.data == "show_settings")
async def cb_show_settings(callback: CallbackQuery):
    user_id = callback.from_user.id

    # Check subscription status
    is_subscribed = await is_user_subscribed(user_id)

    # Show the settings keyboard
    settings_keyboard = kb.get_settings_keyboard(is_subscribed)
    await safe_edit_message_or_answer(
        callback, "⚙️ Настройки бота:", reply_markup=settings_keyboard
    )
    await callback.answer()


# ==================== TIMEZONE HANDLERS ====================


@router.callback_query(F.data == "change_timezone")
async def cb_change_timezone(callback: CallbackQuery):
    # Show timezone change options keyboard
    timezone_keyboard = kb.get_timezone_change_keyboard()
    await safe_edit_message_or_answer(
        callback,
        "Как вы хотите изменить свою таймзону?",
        reply_markup=timezone_keyboard,
    )
    await callback.answer()


@router.callback_query(F.data == "request_location")
async def cb_request_location(callback: CallbackQuery):
    try:
        from aiogram.types import (
            ReplyKeyboardMarkup,
            KeyboardButton,
        )

        location_keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(
                        text="📍 Отправить мое местоположение", request_location=True
                    )
                ],
                [KeyboardButton(text="❌ Отмена")],
            ],
            resize_keyboard=True,
            one_time_keyboard=True,
        )

        await safe_message_answer(
            callback,
            "Пожалуйста, нажмите кнопку ниже, чтобы поделиться своим местоположением. "
            "Я определю вашу таймзону автоматически.",
            reply_markup=location_keyboard,
        )
    except TelegramBadRequest:
        from aiogram.types import (
            ReplyKeyboardMarkup,
            KeyboardButton,
        )

        location_keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(
                        text="📍 Отправить мое местоположение", request_location=True
                    )
                ],
                [KeyboardButton(text="❌ Отмена")],
            ],
            resize_keyboard=True,
            one_time_keyboard=True,
        )

        await safe_message_answer(
            callback,
            "Пожалуйста, нажмите кнопку ниже, чтобы поделиться своим местоположением. "
            "Я определю вашу таймзону автоматически.",
            reply_markup=location_keyboard,
        )

    await callback.answer()


# ==================== LOCATION HANDLERS ====================


# Handler for when user sends their location
@router.message(F.location)
async def handle_user_location(message: Message):
    if message.location is None:
        return  # Can't proceed without location info

    if message.from_user is None:
        return  # Can't proceed without user info
    user_id = message.from_user.id
    latitude = message.location.latitude
    longitude = message.location.longitude

    # Determine timezone based on location
    timezone = await determine_timezone_from_coordinates(latitude, longitude)

    if timezone:
        # Update the user's timezone in the database
        await update_user_timezone(user_id, timezone)
        response_text = f"Ваша таймзона автоматически установлена на {timezone}."
    else:
        # If we can't determine the timezone, default to UTC
        await update_user_timezone(user_id, "UTC")
        response_text = "Не удалось определить таймзону по вашему местоположению. Установлена таймзона по умолчанию (UTC)."

    # Remove the location keyboard and show the main keyboard
    from aiogram.types import ReplyKeyboardRemove

    is_subscribed = await is_user_subscribed(user_id)
    main_keyboard = kb.get_main_keyboard(is_subscribed)

    await message.answer(response_text, reply_markup=ReplyKeyboardRemove())
    await message.answer(
        "Вот клавиатура для управления подпиской:", reply_markup=main_keyboard
    )


# Handler for when user cancels the location request
@router.message(F.text == "❌ Отмена")
async def handle_cancel_location(message: Message):
    if message.from_user is None:
        return  # Can't proceed without user info
    user_id = message.from_user.id

    from aiogram.types import ReplyKeyboardRemove

    is_subscribed = await is_user_subscribed(user_id)
    main_keyboard = kb.get_main_keyboard(is_subscribed)

    await message.answer(
        "Запрос местоположения отменен.", reply_markup=ReplyKeyboardRemove()
    )
    await message.answer(
        "Вот клавиатура для управления подпиской:", reply_markup=main_keyboard
    )


async def determine_timezone_from_coordinates(lat: float, lng: float) -> str:
    """
    Determine timezone from coordinates.
    This is a simplified implementation. In a real application,
    you would use a geolocation API like Google Timezone API.
    """
    # This is a simplified timezone determination based on longitude
    # Each 15 degrees of longitude roughly corresponds to 1 hour difference

    # Calculate the approximate UTC offset based on longitude
    utc_offset_hours = round(lng / 15)

    # Determine a timezone based on the offset
    if -2 <= utc_offset_hours <= 2:
        return "Europe/London"  # GMT/UTC
    elif 3 <= utc_offset_hours <= 5:
        return "Europe/Moscow"  # Moscow time
    elif 6 <= utc_offset_hours <= 8:
        return "Asia/Yekaterinburg"
    elif 9 <= utc_offset_hours <= 11:
        return "Asia/Vladivostok"
    elif 12 <= utc_offset_hours <= 14:
        return "Asia/Kamchatka"
    elif -3 <= utc_offset_hours <= -1:
        return "Europe/London"  # Western European time
    elif -4 <= utc_offset_hours <= -6:
        return "America/New_York"  # US Eastern time
    elif -7 <= utc_offset_hours <= -9:
        return "America/Los_Angeles"  # US Pacific time
    elif -10 <= utc_offset_hours <= -12:
        return "Pacific/Honolulu"  # Hawaii
    else:
        # Create a basic mapping of common coordinates to timezones
        # This is just an approximation
        if 55.75 <= lat <= 56.75 and 37.0 <= lng <= 38.0:  # Moscow
            return "Europe/Moscow"
        elif 40.7 <= lat <= 41.7 and -74.0 <= lng <= -73.0:  # New York
            return "America/New_York"
        elif 35.6 <= lat <= 36.6 and 139.0 <= lng <= 140.0:  # Tokyo
            return "Asia/Tokyo"
        elif 51.0 <= lat <= 52.0 and -0.5 <= lng <= 0.5:  # London
            return "Europe/London"
        elif 34.0 <= lat <= 35.0 and -118.0 <= lng <= -117.0:  # Los Angeles
            return "America/Los_Angeles"
        else:
            # Default to Moscow if in Russia, or UTC otherwise
            if (
                41.0 <= lat <= 82.0 and 19.0 <= lng <= 169.0
            ):  # Approximate Russia coordinates
                return "Europe/Moscow"
            else:
                return "UTC"


# ==================== TIMEZONE SELECTION HANDLERS ====================


@router.callback_query(F.data == "select_timezone")
async def cb_select_timezone(callback: CallbackQuery):
    """Handles the select timezone request."""
    timezone_keyboard = kb.get_timezone_selection_keyboard()
    await safe_edit_message_or_answer(
        callback, "Выберите вашу таймзону из списка:", reply_markup=timezone_keyboard
    )
    await callback.answer()


# Handler for when user selects a specific timezone from the list
@router.callback_query(F.data.startswith("tz_"))
async def cb_select_specific_timezone(callback: CallbackQuery):
    user_id = callback.from_user.id
    # Extract timezone from callback data (format: "tz_Europe/Moscow")
    if callback.data is None:
        await callback.answer("Ошибка: нет данных в callback.", show_alert=True)
        return
    timezone = callback.data[3:]  # Remove "tz_" prefix

    # Update the user's timezone in the database
    await update_user_timezone(user_id, timezone)

    await callback.answer(f"Ваша таймзона установлена на {timezone}.", show_alert=True)

    # Show the main keyboard again
    is_subscribed = await is_user_subscribed(callback.from_user.id)
    keyboard = kb.get_main_keyboard(is_subscribed)
    await safe_edit_reply_markup_or_answer(
        callback, keyboard, "Вот клавиатура для управления подпиской:"
    )


# ==================== CAT HANDLERS ====================


@router.callback_query(F.data == "get_cat")
async def cb_get_cat(callback: CallbackQuery, cat_api_key: str, db_path: str):
    user_id = callback.from_user.id

    # Register user if first interaction
    if not await is_bot_user(user_id):
        await add_bot_user(user_id)

    await callback.answer("Ищу котика...", show_alert=False)
    image_url = await get_cat_image_url(cat_api_key)

    if image_url:
        try:
            # Send cat photo
            await safe_message_answer_photo(
                callback, photo=image_url, caption="Вот ваш случайный котик! ❤️"
            )

            # Send menu with buttons again
            is_subscribed = await is_user_subscribed(user_id)
            keyboard = kb.get_main_keyboard(is_subscribed)

            await safe_message_answer(
                callback, "Что делаем дальше?", reply_markup=keyboard
            )

        except Exception as e:
            logger.error(f"Ошибка отправки фото: {e}")
            await safe_message_answer(
                callback, "Ой, не удалось загрузить котика. Попробуйте еще раз."
            )
    else:
        await safe_message_answer(
            callback, "Что-то пошло не так, котик убежал. Попробуйте позже."
        )
