from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

from database.users import get_all_users

admin_router = Router()


@admin_router.message(Command("admin"))
async def admin_panel(message: Message, db_path: str):
    user_count = len(await get_all_users(db_path))

    text = (
        f"<b>👑 Админ-панель</b>\n\n👥 Подписанных пользователей: <b>{user_count}</b>"
    )

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="📥 Выгрузить ID пользователей", callback_data="admin_export_users"
        )
    )

    await message.answer(text, reply_markup=builder.as_markup())


@admin_router.callback_query(F.data == "admin_export_users")
async def export_users(callback: CallbackQuery, db_path: str):
    await callback.answer("Готовлю файл...", show_alert=False)

    users = await get_all_users(db_path)

    if not users:
        await callback.message.answer("База подписчиков пуста.")
        return

    user_ids_str = "\n".join(map(str, users))

    file_to_send = BufferedInputFile(
        file=user_ids_str.encode("utf-8"), filename="subscribed_users.txt"
    )

    await callback.message.answer_document(
        file_to_send, caption=f"📄 Список ID {len(users)} подписчиков."
    )
