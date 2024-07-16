import sys

import loguru
import os

from aiogram import Router, flags, types, Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.fsm.context import FSMContext

import utils.keyboards as kbs
from handlers.create_unit.states import CreateUnitStates
from utils import api

router = Router()


@router.callback_query(lambda query: query.data == 'create_unit')
@flags.backable()
async def create_unit_callback_handler(query: types.CallbackQuery, state: FSMContext):
    await state.set_state(CreateUnitStates.uid)
    await state.update_data(prev_message=query.message)
    await query.message.edit_text(text='Введите UID пользователя:', reply_markup=kbs.get_just_back_button_keyboard())
    await query.answer()
