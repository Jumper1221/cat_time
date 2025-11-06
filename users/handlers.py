# handlers.py (ИСПРАВЛЕННАЯ ВЕРСИЯ)
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.filters import CommandStart, Command

from database.users import is_user_subscribed, add_user, remove_user, get_all_users
from database.bot_users import is_bot_user, add_bot_user
import users.keyboards as kb
from services.cat_api import get_cat_image_url

# --- Основной роутер для пользователей ---
router = Router()
logger = logging.getLogger(__name__)


@router.message(CommandStart())
async def cmd_start(message: Message, db_path: str):
    user_id = message.from_user.id

    # Check if this is the user's first interaction with the bot
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
        # If admin module is not available, skip
        pass


@router.callback_query(F.data == "subscribe")
async def cb_subscribe(callback: CallbackQuery, db_path: str):
    user_id = callback.from_user.id

    # Check if this is the user's first interaction with the bot
    if not await is_bot_user(user_id):
        await add_bot_user(user_id)

    await add_user(user_id)
    await callback.answer("Вы успешно подписались на рассылку! 🎉", show_alert=True)

    # Show the updated inline keyboard
    keyboard = kb.get_main_keyboard(is_subscribed=True)
    try:
        await callback.message.edit_reply_markup(reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Ошибка обновления клавиатуры: {e}")


@router.callback_query(F.data == "unsubscribe")
async def cb_unsubscribe(callback: CallbackQuery, db_path: str):
    user_id = callback.from_user.id

    # Check if this is the user's first interaction with the bot
    if not await is_bot_user(user_id):
        await add_bot_user(user_id)

    await remove_user(user_id)
    await callback.answer("Вы отписались от рассылки. 😿", show_alert=True)

    # Show the updated inline keyboard
    keyboard = kb.get_main_keyboard(is_subscribed=False)
    try:
        await callback.message.edit_reply_markup(reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Ошибка обновления клавиатуры: {e}")


@router.callback_query(F.data == "get_cat")
async def cb_get_cat(
    callback: CallbackQuery, cat_api_key: str, db_path: str
):  # <-- Добавили db_path
    user_id = callback.from_user.id

    # Check if this is the user's first interaction with the bot
    if not await is_bot_user(user_id):
        await add_bot_user(user_id)

    await callback.answer("Ищу котика...", show_alert=False)
    image_url = await get_cat_image_url(cat_api_key)

    if image_url:
        try:
            # 1. Отправляем фото кота
            await callback.message.answer_photo(
                photo=image_url, caption="Вот ваш случайный котик! ❤️"
            )

            # 2. Снова отправляем меню с кнопками
            is_subscribed = await is_user_subscribed(user_id)
            keyboard = kb.get_main_keyboard(is_subscribed)

            try:
                await callback.message.answer(
                    "Что делаем дальше?", reply_markup=keyboard
                )
            except Exception as e:
                logger.error(f"Ошибка отправки сообщения: {e}")

        except Exception as e:
            logger.error(f"Ошибка отправки фото: {e}")
            try:
                await callback.message.answer(
                    "Ой, не удалось загрузить котика. Попробуйте еще раз."
                )
            except Exception as e:
                logger.error(f"Ошибка отправки сообщения: {e}")
                await callback.answer(
                    "Ой, не удалось загрузить котика. Попробуйте еще раз.",
                    show_alert=True,
                )
    else:
        try:
            await callback.message.answer(
                "Что-то пошло не так, котик убежал. Попробуйте позже."
            )
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения: {e}")
            await callback.answer(
                "Что-то пошло не так, котик убежал. Попробуйте позже.", show_alert=True
            )
