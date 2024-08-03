import sys

import loguru
import os

from aiogram import Router, flags, types, Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.fsm.context import FSMContext
from aiogram.types import InputFile, PhotoSize
from aiogram.utils.formatting import Code, Bold

import config
import telegram_bot.utils.keyboards as kbs
from telegram_bot.utils import api
from encryption.system import decrypt_private_key

router = Router()


@router.callback_query(lambda query: query.data == 'dev_create')
async def dev_callback_handler(query: types.CallbackQuery, state: FSMContext):
    await api.send_unit_command(query.from_user.id, 'create')
    await query.answer()


@router.callback_query(lambda query: query.data == 'dev_get_private')
async def dev_callback_handler(query: types.CallbackQuery, state: FSMContext):
    key = await api.send_unit_command(query.from_user.id, 'get_private_key')
    decrypted = await decrypt_private_key(key, config.BOT_API_TOKEN)
    await query.message.answer(
        f'В целях {Bold("безопасности").as_html()} рекомендуется {Bold("удалить данное сообщение").as_html()}'
        f' после копирования ключа.'
        f'\nПриватный ключ кошелька:\n{Code(decrypted).as_html()}', parse_mode='HTML')
    await query.answer()
