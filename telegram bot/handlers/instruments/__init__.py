from aiogram import Router
from .callbacks import router as callbacks_router
from .messages import router as messages_router

router = Router()

router.include_routers(
    callbacks_router,
    messages_router
)
