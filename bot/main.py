import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.types import BotCommand, BotCommandScopeChat
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN, LOGS_DIR, ADMINS_FILE
from handlers import router
from database.db import init_db
from scheduler import setup_scheduler

# Setup logging
LOGS_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOGS_DIR / "bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def get_admin_ids() -> list[int]:
    if not ADMINS_FILE.exists():
        return []
    with open(ADMINS_FILE, "r") as f:
        return [int(line.strip()) for line in f if line.strip() and not line.startswith("#")]


async def set_bot_commands(bot: Bot):
    # Default commands for all users
    user_commands = [
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="wants", description="Мои хочу"),
        BotCommand(command="stats", description="Статистика"),
        BotCommand(command="help", description="Помощь"),
    ]

    # Admin commands
    admin_commands = user_commands + [
        BotCommand(command="admin_stats", description="Статистика бота"),
        BotCommand(command="admin_export", description="Экспорт данных"),
        BotCommand(command="admin_metric", description="График активности"),
    ]

    # Set default commands for all users
    await bot.set_my_commands(user_commands)

    # Set extended commands for admins
    for admin_id in get_admin_ids():
        try:
            await bot.set_my_commands(
                admin_commands,
                scope=BotCommandScopeChat(chat_id=admin_id)
            )
        except Exception as e:
            logger.warning(f"Could not set commands for admin {admin_id}: {e}")

    logger.info("Bot commands configured")


async def main():
    logger.info("Bot starting...")

    init_db()

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    dp.include_router(router)

    # Set bot commands (Menu Button)
    await set_bot_commands(bot)

    scheduler = setup_scheduler(bot)
    scheduler.start()
    logger.info("Scheduler started")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
