import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from telegram_bot.handlers.command_handlers import router as command_router
from telegram_bot.handlers.callback_handlers import router as general_callbacks_router
from telegram_bot.handlers.dev import router as dev_router
from telegram_bot.handlers.givedays import router as givedays_router
from telegram_bot.handlers.broadcast import router as broadcast_router
from telegram_bot.handlers.instruments import router as instruments_router
from telegram_bot.handlers.sub_extend import router as sub_extend_router
from telegram_bot.handlers.add_proxies import router as add_proxies_router


import config

TOKEN = config.BOT_API_TOKEN


async def main() -> None:
    # Initialize Bot instance with default bot properties which will be passed to all API calls
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    # Register routers
    dp.include_routers(
        command_router,
        general_callbacks_router,
        sub_extend_router,
        givedays_router,
        broadcast_router,
        instruments_router,
        dev_router,
        add_proxies_router
    )

    # Start polling
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
