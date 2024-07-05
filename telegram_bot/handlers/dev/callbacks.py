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
    await api.send_server_command(query.from_user.id, 'create')
    await query.answer()


@router.callback_query(lambda query: query.data == 'dev_start')
async def dev_callback_handler(query: types.CallbackQuery, state: FSMContext):
    await api.send_server_command(query.from_user.id, 'start')
    await query.answer()


@router.callback_query(lambda query: query.data == 'dev_stop')
async def dev_callback_handler(query: types.CallbackQuery, state: FSMContext):
    await api.send_server_command(query.from_user.id, 'stop')
    await query.answer()
