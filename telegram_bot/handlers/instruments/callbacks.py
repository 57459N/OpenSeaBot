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
Для ознакомления с командами рекомендуется прочитать гайд про все функции бота
Если что-то будет не понятно, можете смело писать саппорту <a href="{config.LINK_TO_SUPPORT}">@Помощьник</a>

Основные команды:
\tФлор листер - Выставляет ваши нфт по флору, перебивая другие листинги

\tБидер - Выставляет биды на коллекции, которые вы добавите в бота

\tСканер - Анализируте подходящие коллекции под флип по разным критериям. Основной критерий: актив и желанный % профита с коллекции
'''
    await query.message.edit_text(text=text,
                                  parse_mode='HTML',
                                  reply_markup=kbs.get_just_back_button_keyboard())
    await query.answer()


@router.callback_query(InstrumentCallback.filter(F.act == 'menu'))
@flags.backable()
async def instruments_callback_handler(query: types.CallbackQuery, callback_data: InstrumentCallback):
    await query.message.edit_text(text=f'Меню {callback_data.inst}',
                                  reply_markup=kbs.get_instrument_keyboard(callback_data.inst))
    await query.answer()


@router.callback_query(InstrumentCallback.filter(F.act == 'settings'))
@flags.backable()
async def instruments_settings_callback_handler(query: types.CallbackQuery, callback_data: InstrumentCallback,
                                                state: FSMContext):
    uid = query.from_user.id
    instrument = api.INSTRUMENTS[callback_data.inst]
    settings = await api.send_unit_command(uid, 'get_settings')
    if settings is False:
        await query.answer('Error while getting settings')
        return

    await state.update_data(prev_settings=settings, settings=deepcopy(settings), message=query.message,
                            instrument=instrument, parameter=callback_data.param)

    await query.message.edit_text(text=get_settings_beautiful_list(settings=settings,
                                                                   header=f'Настройки {instrument.name}:'
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
    except KeyError:
        await query.answer()
        await query.message.delete()
        return

    await state.set_state(InstrumentStates.settings_change)
    await state.update_data(parameter=callback_data.param)
    await query.message.edit_text(text=get_settings_beautiful_list(settings=settings,
                                                                   active=callback_data.param,
                                                                   header=f'Настройки {callback_data.inst}:'
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
        m = await query.message.answer('Настройки должны отличаться от предыдущих.')
        await asyncio.sleep(2)
        await query.answer()
        await m.delete()
        return

    instrument = api.INSTRUMENTS[callback_data.inst]
    uid = query.from_user.id

    resp = await api.send_unit_command(uid, 'set_settings', settings)
    match resp.status:
        case 200:
            await query.message.edit_text(f"{instrument.name}'s settings set successfully")
            await go_back(query, state, new_message=True, delete_old_message=False)
        case 400, 404:
            await query.message.answer('Произошла внутренняя ошибка. Пожалуйста обратитесь в поддержку')
        case 409:
            await query.message.answer(await resp.text())

    await query.answer()


@router.callback_query(InstrumentCallback.filter(F.act == 'start'))
async def instruments_start_callback_handler(query: types.CallbackQuery, callback_data: InstrumentCallback):
    instrument = api.INSTRUMENTS[callback_data.inst]
    uid = query.from_user.id

    resp = await api.send_unit_command(uid, 'start')
    match resp.status:
        case 200:
            await query.answer(f'{instrument.name} started')
        case 409:
            await query.answer(await resp.text())
        case 403:
            await query.answer(
                'Ввша подписка неактивна. Вы можете оплатить ее в меню "Информация nо подписке"',
                show_alert=True)
        case 503:
            await query.message.answer(
                'К сожалению вам не предоставили прокси. Обратитесь в поддержку для решения данной проблемы',
                reply_markup=kbs.get_support_keyboard())
        case _:
            await query.message.answer(
                'Ошибка на сервере, попробуйте позже. Если проблема повторяется, обратитесь в поддержку.')
            await query.answer(f'{instrument.name} not started')


@router.callback_query(InstrumentCallback.filter(F.act == 'stop'))
async def instruments_start_callback_handler(query: types.CallbackQuery, callback_data: InstrumentCallback):
    instrument = api.INSTRUMENTS[callback_data.inst]
    uid = query.from_user.id
    resp = await api.send_unit_command(uid, 'stop')
    match resp.status:
        case 200:
            await query.answer(f'{instrument.name} stopped')
        case 409:
            await query.answer(f'{instrument.name} is not running', show_alert=True)
        case _:
            await query.message.answer(
                'Ошибка на сервере, попробуйте позже. Если проблема повторяется, обратитесь в поддержку.')
            await query.answer(f'{instrument.name} not stopped')
