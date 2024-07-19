from copy import copy, deepcopy
from typing import Callable, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.dispatcher.flags import get_flag
from aiogram.types import Message, TelegramObject


class BackableMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: dict[str, Any],
    ) -> Any:

        if isinstance(event, Message):
            message = data.get['prev_message']
        else:
            message = event.message

        if get_flag(data, "backable") is not None:
            state = data['state']
            await data['state'].update_data(previous_state=await state.get_state(),
                                            previous_data=copy(await state.get_data()),
                                            previous_keyboard=message.reply_markup,
                                            previous_text=message.text)

        return await handler(event, data)
