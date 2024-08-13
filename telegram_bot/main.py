import asyncio
import os
import sys

sys.path.append(os.getcwd())

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
from telegram_bot.handlers.create_unit import router as create_unit_router
from telegram_bot.handlers.init_unit import router as init_unit_router
from telegram_bot.handlers.wallet_data import router as wallet_data_router
from telegram_bot.handlers.collections import router as collections_router


import config

TOKEN = config.BOT_API_TOKEN


async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    await bot.delete_webhook(drop_pending_updates=True)

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
        init_unit_router,
        wallet_data_router,
        collections_router,
    )

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
