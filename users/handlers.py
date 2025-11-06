# handlers.py (ИСПРАВЛЕННАЯ ВЕРСИЯ)
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.filters import CommandStart, Command

from database.users import is_user_subscribed, add_user, remove_user, get_all_users
import users.keyboards as kb
from services.cat_api import get_cat_image_url

# --- Основной роутер для пользователей ---
router = Router()
logger = logging.getLogger(__name__)


@router.message(CommandStart())
async def cmd_start(message: Message, db_path: str):
    user_id = message.from_user.id
    is_subscribed = await is_user_subscribed(db_path, user_id)
    await message.answer(
        "Привет! Я бот, который будет присылать тебе котиков 😺",
        reply_markup=kb.get_main_keyboard(is_subscribed),
    )


@router.callback_query(F.data == "subscribe")
async def cb_subscribe(callback: CallbackQuery, db_path: str):
    user_id = callback.from_user.id
    await add_user(db_path, user_id)
    await callback.answer("Вы успешно подписались на рассылку! 🎉", show_alert=True)
    await callback.message.edit_reply_markup(
        reply_markup=kb.get_main_keyboard(is_subscribed=True)
    )


@router.callback_query(F.data == "unsubscribe")
async def cb_unsubscribe(callback: CallbackQuery, db_path: str):
    user_id = callback.from_user.id
    await remove_user(db_path, user_id)
    await callback.answer("Вы отписались от рассылки. 😿", show_alert=True)
    await callback.message.edit_reply_markup(
        reply_markup=kb.get_main_keyboard(is_subscribed=False)
    )


@router.callback_query(F.data == "get_cat")
async def cb_get_cat(
    callback: CallbackQuery, cat_api_key: str, db_path: str
):  # <-- Добавили db_path
    await callback.answer("Ищу котика...", show_alert=False)
    image_url = await get_cat_image_url(cat_api_key)

    if image_url:
        try:
            # 1. Отправляем фото кота
            await callback.message.answer_photo(
                photo=image_url, caption="Вот ваш случайный котик! ❤️"
            )

            # 2. Снова отправляем меню с кнопками
            user_id = callback.from_user.id
            is_subscribed = await is_user_subscribed(db_path, user_id)
            await callback.message.answer(
                "Что делаем дальше?", reply_markup=kb.get_main_keyboard(is_subscribed)
            )

        except Exception as e:
            logger.error(f"Ошибка отправки фото: {e}")
            await callback.message.answer(
                "Ой, не удалось загрузить котика. Попробуйте еще раз."
            )
    else:
        await callback.message.answer(
            "Что-то пошло не так, котик убежал. Попробуйте позже."
        )
