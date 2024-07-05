from aiogram import Router

from telegram_bot.middlwares.backable_query_middleware import BackableMiddleware
from .callbacks import router as callbacks_router
from .messages import router as messages_router

router = Router()
router.include_routers(callbacks_router,
                       messages_router)

router.callback_query.middleware(BackableMiddleware())
router.message.middleware(BackableMiddleware())
