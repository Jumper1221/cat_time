import asyncio
from aiogram import Bot
from aiogram.types import BotCommand
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config.settings import BOT_TOKEN, CAT_API_KEY, DATABASE_NAME, get_admin_ids, logger
from bot.core import create_bot, create_dispatcher
from database.connection import init_db_connection, get_db_connection
from users.handlers import router as user_router
from admin.handlers import admin_router
from admin.filters import IsAdmin
from services.scheduler import send_daily_cats
from admin.keyboards import get_admin_reply_keyboard


async def main():
    if not BOT_TOKEN or not CAT_API_KEY or not DATABASE_NAME:
        logger.critical(
            "Необходимые переменные окружения не установлены! (BOT_TOKEN, CAT_API_KEY, DATABASE_NAME)"
        )
        return

    admin_ids = get_admin_ids()

    # Инициализация базы данных
    db_connection = init_db_connection(DATABASE_NAME)
    await db_connection.init_db()

    bot = create_bot()
    dp = create_dispatcher()

    # Передаем пути и ключи в хэндлеры через middleware
    dp["db_path"] = DATABASE_NAME
    dp["cat_api_key"] = CAT_API_KEY
    dp["bot"] = bot

    # Регистрируем роутеры
    dp.include_router(user_router)

    # Применяем фильтр IsAdmin ко всем хендлерам в admin_router
    admin_router.message.filter(IsAdmin(admin_ids))
    admin_router.callback_query.filter(IsAdmin(admin_ids))
    dp.include_router(admin_router)

    # Настройка и запуск планировщика
    scheduler = AsyncIOScheduler(timezone="UTC")
    # Run the scheduler every hour to check if any users should receive their daily cat
    scheduler.add_job(
        send_daily_cats,
        "cron",
        minute=0,
        args=(bot, DATABASE_NAME, CAT_API_KEY),
    )
    scheduler.start()

    logger.info("Бот запускается...")

    # Устанавливаем команды бота для обычных пользователей (по умолчанию)
    user_commands = [
        BotCommand(command="/start", description="Запустить бота"),
        BotCommand(command="/settings", description="Настройки бота"),
        BotCommand(command="/cat", description="Получить случайного кота"),
    ]
    await bot.set_my_commands(user_commands)
    
    if admin_ids:
        # Устанавливаем команды бота для администраторов (включая пользовательские команды)
        admin_commands = [
            BotCommand(command="/start", description="Запустить бота"),
            BotCommand(command="/settings", description="Настройки бота"),
            BotCommand(command="/cat", description="Получить случайного кота"),
            BotCommand(command="/admin", description="Админ-панель"),
        ]
        # Actually, in aiogram 3.x we need to use BotCommandScopeChat for specific users
        from aiogram.types import BotCommandScopeChat
        for admin_id in admin_ids:
            admin_scope = BotCommandScopeChat(chat_id=admin_id)
            await bot.set_my_commands(admin_commands, scope=admin_scope)

    if admin_ids:
        try:
            # Get user count for admin keyboard
            from database.users import get_all_users
            from database.bot_users import get_all_bot_users

            users = await get_all_users()
            user_count = len(users)
            bot_users = await get_all_bot_users()
            bot_user_count = len(bot_users)

            await bot.send_message(
                admin_ids[0],
                "Бот успешно запущен!",
                reply_markup=get_admin_reply_keyboard(user_count, bot_user_count),
            )
        except Exception as e:
            logger.warning(
                f"Не удалось отправить сообщение администратору ({admin_ids[0]}): {e}"
            )

    # Запускаем бота
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен.")
    except Exception as e:
        logger.critical(f"Критическая ошибка при запуске бота: {e}", exc_info=True)
