import asyncio
from copy import deepcopy

from aiogram import Router, F, types, flags
from aiogram.fsm.context import FSMContext

import config
from telegram_bot.handlers.callbacks_data import InstrumentCallback
from telegram_bot.middlwares.backable_query_middleware import BackableMiddleware

from .states import InstrumentStates
from telegram_bot.utils import api
from telegram_bot.utils.misc import get_settings_beautiful_list, go_back

import telegram_bot.utils.keyboards as kbs

router = Router()
router.callback_query.middleware(BackableMiddleware())

get_settings_map = {
    'Floor Lister': 'floor_lister',
    'Collection Scanner': 'collection_scanner',
    'Collection Bidder': 'collection_bidder'
}


@router.callback_query(InstrumentCallback.filter(F.act == 'info'))
@flags.backable()
async def instruments_callback_handler(query: types.CallbackQuery):
    text = f'''
HERE WILL BE FAQ AND GITBOOK AND LINKS TO OUR RESOURSES
'''
    await query.message.edit_text(text=text,
                                  parse_mode='HTML',
                                  reply_markup=kbs.get_just_back_button_keyboard())
    await query.answer()


@router.callback_query(InstrumentCallback.filter(F.act == 'menu'))
@flags.backable()
async def instruments_callback_handler(query: types.CallbackQuery, callback_data: InstrumentCallback):
    await query.message.edit_text(text=f'Menu dodelat nado {callback_data.inst}',
                                  reply_markup=kbs.get_instrument_keyboard(callback_data.inst))
    await query.answer()


@router.callback_query(InstrumentCallback.filter(F.act == 'settings'))
@flags.backable()
async def instruments_settings_callback_handler(query: types.CallbackQuery, callback_data: InstrumentCallback,
                                                state: FSMContext):
    uid = query.from_user.id
    instrument = api.INSTRUMENTS[callback_data.inst]
    settings = await api.send_unit_command(uid, 'get_settings')
    if isinstance(settings, tuple):
        await query.answer('Error while getting settings')
        return

    await state.update_data(prev_settings=settings, settings=deepcopy(settings), message=query.message,
                            instrument=instrument, parameter=callback_data.param)

    await query.message.edit_text(text=get_settings_beautiful_list(settings=settings,
                                                                   header=f'Settings of {instrument.name}:'
                                                                   ).as_html(),
                                  parse_mode='HTML',
                                  reply_markup=kbs.get_instrument_settings_keyboard(instrument.name, settings.keys()))
    await query.answer()


@router.callback_query(InstrumentCallback.filter(F.act == 'settings_change'))
async def instruments_settings_change_callback_handler(query: types.CallbackQuery, state: FSMContext,
                                                       callback_data: InstrumentCallback):
    try:
        data = await state.get_data()
        settings = data['settings']
        prev_settings = data['prev_settings']
    except KeyError:
        await query.answer()
        await query.message.delete()
        return

    await state.set_state(InstrumentStates.settings_change)
    await state.update_data(parameter=callback_data.param)
    await query.message.edit_text(text=get_settings_beautiful_list(settings=settings,
                                                                   prev_settings=prev_settings,
                                                                   active=callback_data.param,
                                                                   header=f'Settings of {callback_data.inst}:'
                                                                   ).as_html(),
                                  parse_mode='HTML',
                                  reply_markup=kbs.get_instrument_settings_keyboard(callback_data.inst,
                                                                                    settings.keys()))
    await query.answer()


@router.callback_query(InstrumentCallback.filter(F.act == 'settings_finish'))
async def instruments_settings_finish_callback_handler(query: types.CallbackQuery, callback_data: InstrumentCallback,
                                                       state: FSMContext):
    data = await state.get_data()
    settings = data['settings']
    prev_settings = data['prev_settings']
    if settings == prev_settings:
        m = await query.message.answer('<b>❗️ The settings should be different from the previous settings.</b>')
        await asyncio.sleep(2)
        await query.answer()
        await m.delete()
        return

    instrument = api.INSTRUMENTS[callback_data.inst]
    uid = query.from_user.id

    status, text = await api.send_unit_command(uid, 'set_settings', settings)
    match status:
        case 200:
            await query.message.edit_text(f"{instrument.name}'s settings set successfully")
            await go_back(query, state, new_message=True, delete_old_message=False)
        case 400, 404:
            await query.message.answer('<b>🤷‍♂️ An internal error has occurred. Please contact support</b>')
        case 409:
            await query.message.answer(text)

    await query.answer()


@router.callback_query(InstrumentCallback.filter(F.act == 'start'))
async def instruments_start_callback_handler(query: types.CallbackQuery, callback_data: InstrumentCallback):
    instrument = api.INSTRUMENTS[callback_data.inst]
    uid = query.from_user.id

    status, text = await api.send_unit_command(uid, 'start')
    match status:
        case 200:
            await query.answer(text, show_alert=True)
            return
        case 409:
            text = 'Your unit is not initialized. Please contact support'
        case 403:
            text = (
                '<b>Your subscription is inactive. </b>\n\nYou can pay for it in the "Subscription information" menu\n'
                'If you have already paid for a subscription, contact support')
        case 503:
            text = 'Unfortunately you have not been provided with a proxy. Please contact support to solve this problem'
        case _:
            text = 'Error on the server, try again later. If the problem recurs, contact support.'

    await query.message.answer(
        text=text,
        reply_markup=kbs.get_support_keyboard())
    await query.answer()


@router.callback_query(InstrumentCallback.filter(F.act == 'stop'))
async def instruments_start_callback_handler(query: types.CallbackQuery, callback_data: InstrumentCallback):
    instrument = api.INSTRUMENTS[callback_data.inst]
    uid = query.from_user.id
    status, text = await api.send_unit_command(uid, 'stop')
    match status:
        case 200:
            await query.answer(text, show_alert=True)
        case 409:
            await query.answer(f'{instrument.name} is already stopped', show_alert=True)
        case _:
            await query.message.answer(
                'Error on the server, try again later. If the problem recurs, contact support.')
            await query.answer(f'{instrument.name} unstopped')
