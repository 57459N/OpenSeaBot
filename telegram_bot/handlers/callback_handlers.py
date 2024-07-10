import asyncio
from contextlib import suppress
from datetime import datetime, timedelta

from aiogram.exceptions import TelegramBadRequest
from aiogram.utils.formatting import Code
from aiogram import Router, types, F, flags
from aiogram.fsm.context import FSMContext

from telegram_bot.handlers.callbacks_data import PaginationCallback, SelectCallback
from telegram_bot.middlwares.backable_query_middleware import BackableMiddleware
from telegram_bot.middlwares.sub_active_middleware import SubActiveMiddleware
from telegram_bot.utils import api
from telegram_bot.utils.misc import go_back, is_user_admin

import telegram_bot.utils.keyboards as kbs

router = Router()
router.callback_query.middleware(BackableMiddleware())
router.callback_query.middleware(SubActiveMiddleware())


@router.callback_query(PaginationCallback.filter(F.action == "paginate"))
async def paginate_callback_handler(query: types.CallbackQuery, callback_data: PaginationCallback, state: FSMContext):
    data = await state.get_data()
    await query.message.edit_reply_markup(
        reply_markup=kbs.get_choose_keyboard(options=data.get("options", []),
                                             selected=data.get("selected_options", set()),
                                             page=callback_data.page))
    await query.answer()


@router.callback_query(SelectCallback.filter())
async def select_callback_handler(query: types.CallbackQuery, callback_data: SelectCallback, state: FSMContext):
    option = callback_data.option

    data = await state.get_data()
    selected_options = data.get('selected_options', set())

    if option in selected_options:
        selected_options.remove(option)
    else:
        selected_options.add(option)

    await state.update_data(selected_options=selected_options)
    await query.message.edit_reply_markup(reply_markup=kbs.get_choose_keyboard(options=data.get('options'),
                                                                               selected=selected_options,
                                                                               page=callback_data.page))
    await query.answer()


@router.callback_query(lambda query: query.data == 'back')
async def universal_back_callback_handler(query: types.CallbackQuery, state: FSMContext):
    await go_back(query, state)


@router.callback_query(lambda query: query.data == 'confirm_no')
async def cancel_callback_handler(query: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await query.message.delete()
    await query.answer()


@router.callback_query(lambda query: query.data == 'delete_message')
async def noop_callback_handler(query: types.CallbackQuery, state: FSMContext):
    # await state.clear()
    await query.message.delete()
    await query.answer()


# Welcome menu #

@router.callback_query(lambda query: query.data == 'sub_info')
@flags.backable()
@router.callback_query(lambda query: query.data == 'sub_info_reload')
async def sub_info_callback_handler(query: types.CallbackQuery):
    sub_info = await api.get_user_subscription_info_by_id(query.from_user.id)
    status = 'Активна' if sub_info.get('status', 'No info').lower() == 'active' else 'Не активна'
    days_left = sub_info.get('days_left', 'No info')
    balance = sub_info.get('balance', 'No info')

    text = f'''
Привет, @{query.from_user.username}!

С помощью данного меню ты можешь продлить подписку. Нажми на кнопку ниже, чтобы получить адрес для оплаты.

Статус подписки: {status}
Осталось дней до конца подписки: {days_left}
Ваш баланс: {balance}
'''
    with suppress(TelegramBadRequest):
        await query.message.edit_text(text=text, reply_markup=kbs.get_sub_info_keyboard())
    await query.answer()


@router.callback_query(lambda query: query.data == 'get_user_tgid')
async def extend_sub_callback_handler(query: types.CallbackQuery):
    await query.message.answer(**Code(str(query.from_user.id)).as_kwargs())
    await query.answer()


@router.callback_query(lambda query: query.data == 'sub_manage')
@flags.sub_active()
@flags.backable()
async def extend_sub_callback_handler(query: types.CallbackQuery, state: FSMContext):
    text = '''
    Добро пожаловать в панель управления нашим ботом.
    
Здесь вы можете настраивать и запускать все функции данного бота.'''

    await query.message.edit_text(text=text, reply_markup=kbs.get_instruments_keyboard())
    await query.answer()


# Admin menu #
@router.callback_query(lambda query: query.data == 'admin_menu')
async def admin_menu_callback_handler(query: types.CallbackQuery):
    await query.message.answer(text='Админ меню', reply_markup=kbs.get_admin_menu_keyboard())
    await query.answer()


@router.callback_query(lambda query: query.data == 'dev')
async def dev_menu_callback_handler(query: types.CallbackQuery):
    await query.message.answer(text='Dev', reply_markup=kbs.get_dev_keyboard())
    await query.answer()
