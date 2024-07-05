import logging
import os

from aiogram import Router, flags, types, Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.fsm.context import FSMContext
from aiogram.types import InputFile, PhotoSize

import telegram_bot.utils.keyboards as kbs
from telegram_bot.utils import api

router = Router()


@router.callback_query(lambda query: query.data == 'dev_create')
async def dev_callback_handler(query: types.CallbackQuery, state: FSMContext):
    proxies = await api.get_proxies()
    key = await api.get_private_key(query.from_user.id)
    await api.create_unit(query.from_user.id, key, proxies)

    await query.answer()
