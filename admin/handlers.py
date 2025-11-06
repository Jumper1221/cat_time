from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.filters import Command

from database.users import get_all_users
from database.bot_users import get_all_bot_users, get_non_subscribed_bot_users
from admin.keyboards import get_admin_keyboard, get_admin_reply_keyboard

admin_router = Router()


@admin_router.message(Command("admin"))
async def admin_panel(message: Message, db_path: str):
    user_count = len(await get_all_users())
    bot_user_count = len(await get_all_bot_users())

    text = (
        f"<b>👑 Админ-панель</b>\n\n"
        f"👥 Подписанных пользователей: <b>{user_count}</b>\n"
        f"😺 Всего пользователей бота: <b>{bot_user_count}</b>"
    )

    # Use the admin inline keyboard
    keyboard = get_admin_keyboard(user_count, bot_user_count)

    await message.answer(text, reply_markup=keyboard)

    # Also send the reply keyboard for admins
    reply_keyboard = get_admin_reply_keyboard(user_count, bot_user_count)
    await message.answer("Админ-панель:", reply_markup=reply_keyboard)


# Old handlers removed as they are no longer needed with the new keyboard implementation


# New handlers for the updated admin panel functionality
@admin_router.callback_query(F.data == "admin_show_subscribers")
async def show_subscribers_callback(callback: CallbackQuery, db_path: str, bot: Bot):
    await callback.answer()
    users = await get_all_users()

    if not users:
        await bot.send_message(callback.from_user.id, "База подписчиков пуста.")
        return

    user_ids_str = "\n".join(map(str, users))
    await bot.send_message(
        callback.from_user.id, f"Список ID подписчиков:\n\n{user_ids_str}"
    )


@admin_router.message(F.text.contains("Количество подписчиков"))
async def show_subscribers_message(message: Message, db_path: str):
    users = await get_all_users()

    if not users:
        await message.answer("База подписчиков пуста.")
        return

    user_ids_str = "\n".join(map(str, users))
    await message.answer(f"Список ID подписчиков:\n\n{user_ids_str}")


@admin_router.callback_query(F.data == "admin_show_all_users")
async def show_all_users_callback(callback: CallbackQuery, db_path: str, bot: Bot):
    await callback.answer()
    bot_users = await get_all_bot_users()

    if not bot_users:
        await bot.send_message(callback.from_user.id, "База пользователей бота пуста.")
        return

    bot_user_ids_str = "\n".join(map(str, bot_users))
    await bot.send_message(
        callback.from_user.id,
        f"Список ID всех пользователей бота:\n\n{bot_user_ids_str}",
    )


@admin_router.message(F.text.contains("Всего пользователей"))
async def show_all_users_message(message: Message, db_path: str):
    bot_users = await get_all_bot_users()

    if not bot_users:
        await message.answer("База пользователей бота пуста.")
        return

    bot_user_ids_str = "\n".join(map(str, bot_users))
    await message.answer(f"Список ID всех пользователей бота:\n\n{bot_user_ids_str}")


@admin_router.callback_query(F.data == "admin_export_data")
async def export_data_callback(callback: CallbackQuery, db_path: str, bot: Bot):
    await callback.answer("Готовлю файлы...", show_alert=False)

    # Get subscribed and non-subscribed users
    subscribed_users = await get_all_users()
    non_subscribed_users = await get_non_subscribed_bot_users()

    # Send file with subscribed users
    if subscribed_users:
        subscribed_ids_str = "\n".join(map(str, subscribed_users))
        subscribed_file = BufferedInputFile(
            file=subscribed_ids_str.encode("utf-8"), filename="subscribed_users.txt"
        )
        await bot.send_document(
            callback.from_user.id,
            subscribed_file,
            caption=f"📄 Список ID {len(subscribed_users)} подписчиков.",
        )
    else:
        await bot.send_message(
            callback.from_user.id, "Нет подписанных пользователей для выгрузки."
        )

    # Send file with non-subscribed users
    if non_subscribed_users:
        non_subscribed_ids_str = "\n".join(map(str, non_subscribed_users))
        non_subscribed_file = BufferedInputFile(
            file=non_subscribed_ids_str.encode("utf-8"),
            filename="non_subscribed_users.txt",
        )
        await bot.send_document(
            callback.from_user.id,
            non_subscribed_file,
            caption=f"📄 Список ID {len(non_subscribed_users)} не подписанных пользователей.",
        )
    else:
        await bot.send_message(
            callback.from_user.id, "Нет неподписанных пользователей для выгрузки."
        )


@admin_router.message(F.text == "Выгрузить данные")
async def export_data_message(message: Message, db_path: str):
    # Get subscribed and non-subscribed users
    subscribed_users = await get_all_users()
    non_subscribed_users = await get_non_subscribed_bot_users()

    # Send file with subscribed users
    if subscribed_users:
        subscribed_ids_str = "\n".join(map(str, subscribed_users))
        subscribed_file = BufferedInputFile(
            file=subscribed_ids_str.encode("utf-8"), filename="subscribed_users.txt"
        )
        await message.answer_document(
            subscribed_file,
            caption=f"📄 Список ID {len(subscribed_users)} подписчиков.",
        )
    else:
        await message.answer("Нет подписанных пользователей для выгрузки.")

    # Send file with non-subscribed users
    if non_subscribed_users:
        non_subscribed_ids_str = "\n".join(map(str, non_subscribed_users))
        non_subscribed_file = BufferedInputFile(
            file=non_subscribed_ids_str.encode("utf-8"),
            filename="non_subscribed_users.txt",
        )
        await message.answer_document(
            non_subscribed_file,
            caption=f"📄 Список ID {len(non_subscribed_users)} не подписанных пользователей.",
        )
    else:
        await message.answer("Нет неподписанных пользователей для выгрузки.")
