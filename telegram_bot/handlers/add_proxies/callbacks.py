import asyncio

from aiogram import Router, types, flags
from aiogram.fsm.context import FSMContext

from telegram_bot.handlers.add_proxies.states import AddIdleProxiesStates
from telegram_bot.utils import api

import utils.keyboards as kbs

router = Router()


@router.callback_query(lambda query: query.data == 'add_proxies')
@flags.backable()
async def add_proxies_menu_callback_handler(query: types.CallbackQuery, state: FSMContext):
    await state.set_state(AddIdleProxiesStates.to_who)
    await query.message.edit_text('Куда добавить прокси?', reply_markup=kbs.get_to_who_add_proxies_keyboard())
    await query.answer()


@router.callback_query(lambda query: query.data == 'add_proxies_idle', AddIdleProxiesStates.to_who)
@flags.backable()
async def add_proxies_idle_callback_handler(query: types.CallbackQuery, state: FSMContext):
    await state.update_data(proxies=None)
    await state.set_state(AddIdleProxiesStates.list)

    await query.message.edit_text(
        'Отправьте список проксей:\n'
        '\tКаждая новая строка будет расценена как отдельная ссылка\n'
        '\tВ сообщении должно быть максимум 4096 символов\n'
        '\tДля отправки неограниченного количества ссылок отправьте txt файл',
        reply_markup=kbs.get_adding_proxies_keyboard())
    await query.answer()


@router.callback_query(lambda query: query.data == 'add_proxies_finish', AddIdleProxiesStates.list)
async def add_proxies_finish_callback_handler(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    proxies = data.get('proxies', None)
    if proxies is None:
        await query.answer('Список проксей пуст. Добавьте хотя бы одну ссылку', show_alert=True)
        return

    await api.add_proxies(proxies)

    await query.message.delete()
    await state.clear()
    await query.answer()


@router.callback_query(lambda query: query.data == 'dev_add_proxies')
async def add_proxies_idle_callback_handler(query: types.CallbackQuery, state: FSMContext):
    proxies = ['proxy1', 'proxy2', 'proxy3']

    await api.add_proxies(proxies)

    await state.clear()
    await query.answer()