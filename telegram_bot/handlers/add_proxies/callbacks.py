import asyncio

from aiogram import Router, types, flags, F
from aiogram.fsm.context import FSMContext

from handlers.callbacks_data import PaginationCallback
from telegram_bot.handlers.add_proxies.states import AddProxiesStates
from telegram_bot.utils import api

import utils.keyboards as kbs

router = Router()


@router.callback_query(lambda query: query.data == 'add_proxies')
@flags.backable()
async def add_proxies_menu_callback_handler(query: types.CallbackQuery, state: FSMContext):
    await state.set_state(AddProxiesStates.to_who)
    await query.message.edit_text('Куда добавить прокси?', reply_markup=kbs.get_to_who_add_proxies_keyboard())
    await query.answer()


@router.callback_query(lambda query: query.data == 'add_proxies_idle', AddProxiesStates.to_who)
@flags.backable()
async def add_proxies_idle_callback_handler(query: types.CallbackQuery, state: FSMContext):
    await state.update_data(proxies=None, to_who='idle')
    await state.set_state(AddProxiesStates.list)

    await query.message.edit_text(
        'Отправьте список проксей:\n'
        '\tКаждая новая строка будет расценена как отдельная ссылка\n'
        '\tВ сообщении должно быть максимум 4096 символов\n'
        '\tДля отправки неограниченного количества ссылок отправьте txt файл',
        reply_markup=kbs.get_adding_proxies_keyboard())
    await query.answer()


@router.callback_query(lambda query: query.data == 'add_proxies_user', AddProxiesStates.to_who)
@flags.backable()
async def add_proxies_user_callback_handler(query: types.CallbackQuery, state: FSMContext):
    await state.set_state(AddProxiesStates.user)
    options = sorted(list(map(str, (await api.get_user_ids()))))
    selected_options = set()
    await state.update_data(proxies=None, to_who='user', options=options, selected_options=selected_options)
    await query.message.edit_text(
        'Выберите одного пользователя',
        reply_markup=kbs.get_choose_keyboard(options=options, selected=list(selected_options), page=0))
    await query.answer()


@router.callback_query(PaginationCallback.filter(F.action == "end"), AddProxiesStates.user)
async def add_proxies_user_end_callback_handler(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected: None | set = data.get('selected_options', None)
    if selected is None or len(selected) != 1:
        await query.answer('Выберите одного пользователя', show_alert=True)
    else:
        await state.set_state(AddProxiesStates.list)
        await state.update_data(user_id=next(iter(selected)))
        await query.message.edit_text(
            'Отправьте список проксей:\n'
            '\tКаждая новая строка будет расценена как отдельная ссылка\n'
            '\tВ сообщении должно быть максимум 4096 символов\n'
            '\tДля отправки неограниченного количества ссылок отправьте txt файл',
            reply_markup=kbs.get_adding_proxies_keyboard())
        await query.answer()


@router.callback_query(lambda query: query.data == 'add_proxies_finish', AddProxiesStates.list)
async def add_proxies_list_callback_handler(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    to_who = data.get('to_who')
    proxies = data.get('proxies', None)
    uid = None
    if proxies is None or len(proxies) == 0:
        await query.answer('Добавьте хотя бы одну ссылку', show_alert=True)
        return

    if to_who == 'user':
        uid = data.get('user_id', None)

    status, text = await api.add_proxies(proxies, uid)

    if status == 200:
        await query.message.edit_text('Прокси добавлены')
        await asyncio.sleep(3)
        await query.message.delete()
    else:
        await query.message.edit_text(text)

    await query.answer()


