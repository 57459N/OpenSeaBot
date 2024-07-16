import sys

import loguru
import os

from aiogram import Router, flags, types, Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.fsm.context import FSMContext

import utils.keyboards as kbs
from handlers.create_unit.states import InitUnitStates
from utils import api

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

    # todo: activate units via clicking inline button with its id and username
    inactive_units = '\n\t'.join([k for k, v in units.items() if not v])
    await query.message.answer(f'Неактивные юниты:\n\t{inactive_units}')
    await query.answer()
