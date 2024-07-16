import asyncio
import os
import sys

sys.path.append(os.getcwd())

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from handlers.command_handlers import router as command_router
from handlers.callback_handlers import router as general_callbacks_router
from handlers.dev import router as dev_router
from handlers.givedays import router as givedays_router
from handlers.broadcast import router as broadcast_router
from handlers.instruments import router as instruments_router
from handlers.sub_extend import router as sub_extend_router
from handlers.add_proxies import router as add_proxies_router
from handlers.create_unit import router as create_unit_router


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
        add_proxies_router,
        create_unit_router,
    )

    # Start polling
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
