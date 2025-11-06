from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.filters import Command

from database.users import get_all_users
from admin.keyboards import get_admin_keyboard, get_admin_reply_keyboard

admin_router = Router()


@admin_router.message(Command("admin"))
async def admin_panel(message: Message, db_path: str):
    user_count = len(await get_all_users(db_path))

    text = (
        f"<b>👑 Админ-панель</b>\n\n👥 Подписанных пользователей: <b>{user_count}</b>"
    )

    # Use the admin inline keyboard
    keyboard = get_admin_keyboard()

    await message.answer(text, reply_markup=keyboard)

    # Also send the reply keyboard for admins
    reply_keyboard = get_admin_reply_keyboard(user_count)
    await message.answer("Админ-панель:", reply_markup=reply_keyboard)


@admin_router.message(F.text == "📥 Выгрузить ID пользователей")
async def export_users_message(message: Message, db_path: str):
    users = await get_all_users(db_path)

    if not users:
        await message.answer("База подписчиков пуста.")
        return

    user_ids_str = "\n".join(map(str, users))

    file_to_send = BufferedInputFile(
        file=user_ids_str.encode("utf-8"), filename="subscribed_users.txt"
    )

    await message.answer_document(
        file_to_send, caption=f"📄 Список ID {len(users)} подписчиков."
    )


@admin_router.message(F.text == "📋 Показать всех подписчиков")
async def show_all_subscribers(message: Message, db_path: str):
    users = await get_all_users(db_path)
    
    if not users:
        await message.answer("База подписчиков пуста.")
        return
    
    user_ids_str = "\n".join(map(str, users))
    await message.answer(f"Список ID подписчиков:\n\n{user_ids_str}")


@admin_router.callback_query(F.data == "admin_export_users")
async def export_users_callback(callback: CallbackQuery, db_path: str, bot: Bot):
    await callback.answer("Готовлю файл...", show_alert=False)
    
    users = await get_all_users(db_path)

    if not users:
        await bot.send_message(callback.from_user.id, "База подписчиков пуста.")
        return

    user_ids_str = "\n".join(map(str, users))

    file_to_send = BufferedInputFile(
        file=user_ids_str.encode("utf-8"), filename="subscribed_users.txt"
    )

    await bot.send_document(
        callback.from_user.id,
        file_to_send,
        caption=f"📄 Список ID {len(users)} подписчиков."
    )
