import sys
from contextlib import suppress

import loguru
import os

from aiogram import Router, flags, types, Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.fsm.context import FSMContext

import utils.keyboards as kbs
from handlers.callbacks_data import UnitCallbackData
from telegram_bot.handlers.create_unit.states import InitUnitStates
from telegram_bot.utils import api

router = Router()


@router.callback_query(lambda query: query.data == 'init_unit')
@flags.backable()
async def create_unit_callback_handler(query: types.CallbackQuery, state: FSMContext):
    units = await api.get_units_status()
    if isinstance(units, tuple):
        loguru.logger.warning(f'Init unit: got wrong unit data {units}')
        await query.message.answer('Ошибка при получении стасусов юнитов')
        await query.answer()
        return
    await state.update_data(units=units)
    await query.message.edit_text('Юниты', reply_markup=kbs.get_units_keyboard(units))
    await query.answer()


@router.callback_query(UnitCallbackData.filter())
@flags.backable()
async def init_unit_callback_handler(query: types.CallbackQuery, callback_data: UnitCallbackData, state: FSMContext):
    uid = callback_data.uid
    action = callback_data.action

    data = await state.get_data()
    units = data.get('units')

    status, text = await api.unit_init_deinit(uid, action)
    if 200 <= status < 300:
        units[uid] = action
    else:
        await query.answer(text, show_alert=True)
        return

    await state.update_data(units=units)
    with suppress(TelegramBadRequest):
        await query.message.edit_text('Юниты', reply_markup=kbs.get_units_keyboard(units))
    await query.answer()
