import asyncio

from aiogram import Router, types
from aiogram.fsm.context import FSMContext

from .states import InstrumentStates

import utils.keyboards as kbs
from utils.misc import get_settings_beautiful_list

router = Router()


@router.message(InstrumentStates.settings_change)
async def floor_lister_message_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    settings = data['settings']
    parameter = data['parameter']
    settings_message: types.Message = data['message']
    instrument = data['instrument']

    if settings[parameter] == message.text:
        m = await message.answer('Значение должно отличаться от предыдущего.')
        await asyncio.sleep(2)
        await m.delete()
        return

    settings[parameter] = message.text

    await state.update_data(settings=settings)

    await settings_message.edit_text(text=get_settings_beautiful_list(settings=settings,
                                                                      active=parameter,
                                                                      header='Настройки Floor Lister:').as_html(),
                                     parse_mode='HTML',
                                     reply_markup=kbs.get_instrument_settings_keyboard(instrument.name,
                                                                                       settings.keys()))
