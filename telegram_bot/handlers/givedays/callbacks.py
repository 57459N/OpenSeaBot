import asyncio

from aiogram import flags, types, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext

import utils.keyboards as kbs
from handlers.callbacks_data import PaginationCallback
from handlers.givedays.states import GiveDaysStates
from middlwares.backable_query_middleware import BackableMiddleware
from utils import api

router = Router()


@router.callback_query(lambda query: query.data == 'givedays')
@flags.backable()
async def givedays__callback_handler(query: types.CallbackQuery, state: FSMContext):
    text = 'Кому вы хотите выдать дни?'
    kb = kbs.get_givedays_type_keyboard()

    await state.set_state(GiveDaysStates.main)
    await query.message.edit_text(text=text, reply_markup=kb)
    await query.answer()


@router.callback_query(lambda query: query.data in ['givedays_all', 'givedays_active'], GiveDaysStates.main)
@flags.backable()
async def givedays_who_callback_handler(query: types.CallbackQuery, state: FSMContext):
    await state.set_state(GiveDaysStates.amount)
    to_who = query.data.split('_')[1]
    username_to_id = {u.username: u.id for u in await api.get_users(query.bot, to_who)}
    await state.update_data(to_who=to_who, prev_message=query.message, username_to_id=username_to_id)
    await query.message.edit_text(text='Введите или выберите количество дней, которое нужно выдать',
                                  reply_markup=kbs.get_givedays_amount_keyboard())
    await query.answer()


@router.callback_query(lambda query: query.data == 'givedays_usernames', GiveDaysStates.main)
@flags.backable()
async def givedays_usernames_callback_handler(query: types.CallbackQuery, state: FSMContext):
    await state.update_data(to_who='usernames')

    users = await api.get_users(query.bot)
    username_to_id = {u.username: u.id for u in users if u.username}
    await state.update_data(prev_message=query.message, username_to_id=username_to_id)

    await state.set_state(GiveDaysStates.usernames)
    await query.message.edit_text(
        text='Выберите или введите каждое имя пользователя с новой строки после чего нажмите `Готово`',
        reply_markup=kbs.get_usernames_keyboard())
    await query.answer()


@router.callback_query(lambda query: query.data == 'givedays_usernames_enter', GiveDaysStates.usernames)
@flags.backable()
async def givedays_usernames_choose_callback_handler(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    messages_to_delete = data.get('messages_to_delete', [])
    if messages_to_delete:
        for message in messages_to_delete:
            try:
                await message.delete()
            except TelegramBadRequest:
                pass

        await state.set_state(GiveDaysStates.amount)
        await query.message.edit_text(text='Введите или выберите количество дней, которое нужно выдать',
                                      reply_markup=kbs.get_givedays_amount_keyboard())
        await query.answer()
    else:
        error_message = await query.message.answer('Введите хотя бы одного пользователя')
        await asyncio.sleep(1)
        await error_message.delete()


@router.callback_query(lambda query: query.data == 'givedays_usernames_choose', GiveDaysStates.usernames)
@flags.backable()
async def givedays_usernames_choose_callback_handler(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    username_to_id = data['username_to_id']

    options = list(username_to_id.keys())
    await state.set_state(GiveDaysStates.choosing_usernames)
    await state.update_data(options=options, selected_options=set(), username_to_id=username_to_id)
    await query.message.edit_text(text='Выберите пользователей:',
                                  reply_markup=kbs.get_choose_keyboard(options=options))
    await query.answer()


@router.callback_query(PaginationCallback.filter(F.action == "end"), GiveDaysStates.choosing_usernames)
@flags.backable()
async def end_selection_callback_handler(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected_usernames = list(data.get("selected_options", set()))
    if len(selected_usernames) == 0:
        await query.answer('Выберите хотя бы одного пользователя', show_alert=True)
        return

    await state.set_state(GiveDaysStates.amount)
    await state.update_data(usernames=selected_usernames, prev_message=query.message)
    await query.message.edit_text(text='Введите или выберите количество дней, которое нужно выдать',
                                  reply_markup=kbs.get_givedays_amount_keyboard())
    await query.answer()


@router.callback_query(lambda query: 'givedays_amount' in query.data, GiveDaysStates.amount)
@flags.backable()
async def givedays_amount_callback_handler(query: types.CallbackQuery, state: FSMContext):
    amount = query.data.split('_')[-1]

    data = await state.get_data()
    username_to_id: dict = data['username_to_id']

    sep = '\n\t'
    text = f'''
Вы уверены, что хотите выдать дни?
Кому: {sep + sep.join(username_to_id.keys())} 
Сколько: {amount}
'''

    await state.update_data(amount=amount)
    await state.set_state(GiveDaysStates.confirm)
    await query.message.edit_text(text=text, reply_markup=kbs.get_confirm_keyboard())
    await query.answer()


@router.callback_query(lambda query: query.data == 'confirm_yes', GiveDaysStates.confirm)
async def givedays_confirm_callback_handler(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    amount = data['amount']
    usernames = data.get('usernames')
    username_to_id = data['username_to_id']

    # if usernames was selected or entered, else all users filters on get_users stage
    if usernames is not None:
        uids = [username_to_id[uname] for uname in usernames]
    else:
        uids = list(username_to_id.values())

    errors = await api.give_days(uids, amount=amount)

    text = f'Дни успешно выданы {len(uids) - len(errors)} пользователям\n\n'
    if errors:
        text += 'Ошибки:\n\t' + '\n\t'.join([f'{uid} : {err}' for uid, err in errors.items()])
    await query.message.answer(text)

    await state.clear()
    await query.answer()
    await query.message.delete()
