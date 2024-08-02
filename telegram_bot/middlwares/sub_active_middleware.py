from copy import copy
from typing import Callable, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.dispatcher.flags import get_flag
from aiogram.types import Message, TelegramObject

from telegram_bot.utils import api


class SubActiveMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: dict[str, Any],
    ) -> Any:

        if get_flag(data, "sub_active") is not None and 'from_user' in event.model_fields_set:
            uid = event.from_user.id
            if await api.is_users_sub_active(uid):
                return await handler(event, data)
            else:
                await event.answer('Ваша подписка неактивна', show_alert=True)
                # await event.bot.send_message(chat_id=uid, text='Ваша подписка неактивна')

        else:
            return await handler(event, data)
