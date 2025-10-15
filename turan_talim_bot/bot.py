import asyncio
import logging
import sys
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram.client.default import DefaultBotProperties

from config import Config
from utils.logger import setup_logger
from handlers import teacher, student
from database import init_db

# Setup logger
logger = setup_logger("turan_talim_bot")

# Webhook settings
WEBHOOK_PATH = Config.WEBHOOK_PATH
WEBHOOK_URL = Config.WEBHOOK_URL

async def on_startup(bot: Bot, app: web.Application) -> None:
    """
    Startup handler for webhook setup
    """
    # Initialize database
    await init_db()
    
    # Set webhook
    webhook_info = await bot.get_webhook_info()
    
    if webhook_info.url != WEBHOOK_URL:
        await bot.set_webhook(url=WEBHOOK_URL)
        logger.info(f"Webhook set to {WEBHOOK_URL}")
    else:
        logger.info(f"Webhook is already set to {WEBHOOK_URL}")
    
    # Send test message to admin
    if Config.ADMIN_ID:
        try:
            await bot.send_message(
                Config.ADMIN_ID, 
                "✅ TuranTalim bot started successfully with webhook!"
            )
        except Exception as e:
            logger.error(f"Failed to send startup message to admin: {e}")
    
    logger.info("Bot started successfully!")

async def on_shutdown(bot: Bot, app: web.Application) -> None:
    """
    Shutdown handler for cleanup
    """
    # Remove webhook
    await bot.delete_webhook()
    
    # Close bot session
    await bot.session.close()
    
    logger.info("Bot stopped. Webhook removed.")

def create_app() -> web.Application:
    """
    Create and configure aiohttp application
    """
    # Check configuration
    if not Config.validate():
        logger.error("Invalid configuration. Please check your environment variables.")
        sys.exit(1)
    
    # Create bot instance with defaults
    bot = Bot(
        token=Config.BOT_TOKEN, 
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # Setup FSM storage
    storage = MemoryStorage()
    
    # Create dispatcher
    dp = Dispatcher(storage=storage)
    
    # Register routers
    dp.include_router(teacher.router)
    dp.include_router(student.router)
    
    # Create web application
    app = web.Application()
    app["bot"] = bot
    
    # Setup webhook handler
    webhook_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_handler.register(app, path=WEBHOOK_PATH)
    
    # Register startup and shutdown handlers
    async def app_startup(app: web.Application) -> None:
        await on_startup(app["bot"], app)
    
    async def app_shutdown(app: web.Application) -> None:
        await on_shutdown(app["bot"], app)
    
    app.on_startup.append(app_startup)
    app.on_shutdown.append(app_shutdown)
    
    # Setup aiogram application
    setup_application(app, dp, bot=bot)
    
    return app

async def polling_mode():
    """
    Start bot in polling mode (for development)
    """
    # Create bot instance with defaults
    bot = Bot(
        token=Config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # Setup FSM storage
    storage = MemoryStorage()
    
    # Create dispatcher
    dp = Dispatcher(storage=storage)
    
    # Register routers
    dp.include_router(teacher.router)
    dp.include_router(student.router)
    
    # Initialize database
    await init_db()
    
    # Start polling
    logger.info("Starting bot in polling mode...")
    await dp.start_polling(bot)

def main():
    """
    Main entry point
    """
    if len(sys.argv) > 1 and sys.argv[1] == "poll":
        # Polling mode
        logger.info("Starting in polling mode")
        asyncio.run(polling_mode())
    else:
        # Webhook mode
        logger.info(f"Starting in webhook mode (path: {WEBHOOK_PATH}, url: {WEBHOOK_URL})")
        app = create_app()
        web.run_app(
            app,
            host=Config.WEBHOOK_HOST,
            port=Config.WEBHOOK_PORT
        )

if __name__ == "__main__":
    main()
