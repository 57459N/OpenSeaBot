import asyncio
import re

from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.utils.formatting import Code

from .states import InstrumentStates

import telegram_bot.utils.keyboards as kbs
from telegram_bot.utils.misc import get_settings_beautiful_list

router = Router()


@router.message(InstrumentStates.settings_change)
async def instrument_settings_message_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    settings = data['settings']
    prev_settings = data['prev_settings']
    parameter = data['parameter']
    settings_message: types.Message = data['message']
    instrument = data['instrument']

    text = message.text
    is_bad = True
    if settings[parameter] == text:
        answer = "New value can't be the same as an old one."
    elif not re.sub(r'[.,]', '', text).isdigit():
        answer = f'Value must be a number. For example {Code("777").as_html()} or {Code("3.14").as_html()}'
    else:
        is_bad = False

    await message.delete()

    if is_bad:
        m = await message.answer(answer, parse_mode='HTML')
        await asyncio.sleep(3)
        await m.delete()
        return

    settings[parameter] = text
    await state.update_data(settings=settings)

    answer = get_settings_beautiful_list(
        settings=settings,
        prev_settings=prev_settings,
        active=parameter,
        header=f'Settings of {instrument.name}:'
    ).as_html()
    kb = (kbs.get_instrument_settings_keyboard(instrument.name, settings.keys()))
    await settings_message.edit_text(text=answer, reply_markup=kb, parse_mode='HTML')
