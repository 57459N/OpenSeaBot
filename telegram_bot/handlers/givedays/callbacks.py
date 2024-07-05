import asyncio

from aiogram import flags, types, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext

import telegram_bot.utils.keyboards as kbs
from telegram_bot.handlers.callbacks_data import PaginationCallback
from telegram_bot.handlers.givedays.states import GiveDaysStates
from telegram_bot.middlwares.backable_query_middleware import BackableMiddleware
from telegram_bot.utils import api

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
    await state.update_data(to_who=query.data.split('_')[1], prev_message=query.message)
    await query.message.edit_text(text='Введите или выберите количество дней, которое нужно выдать',
                                  reply_markup=kbs.get_givedays_amount_keyboard())
    await query.answer()


@router.callback_query(lambda query: query.data == 'givedays_usernames', GiveDaysStates.main)
@flags.backable()
async def givedays_usernames_callback_handler(query: types.CallbackQuery, state: FSMContext):
    await state.update_data(to_who='usernames')

    await state.set_state(GiveDaysStates.usernames)
    await state.update_data(prev_message=query.message)
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
    usernames = await api.get_usernames(data['to_who'])
    await state.set_state(GiveDaysStates.choosing_usernames)
    await state.update_data(options=usernames, selected_options=set())
    await query.message.edit_text(text='Выберите пользователей:',
                                  reply_markup=kbs.get_choose_keyboard(options=usernames))
    await query.answer()


@router.callback_query(PaginationCallback.filter(F.action == "end"), GiveDaysStates.choosing_usernames)
@flags.backable()
async def end_selection_callback_handler(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected_usernames = list(data.get("selected_options", set()))

    await state.set_state(GiveDaysStates.amount)
    await state.update_data(usernames=selected_usernames, prev_message=query.message)
    await query.message.edit_text(text='Введите или выберите количество дней, которое нужно выдать',
                                  reply_markup=kbs.get_givedays_amount_keyboard())
    await query.answer()


@router.callback_query(lambda query: 'givedays_amount' in query.data, GiveDaysStates.amount)
@flags.backable()
async def givedays_amount_callback_handler(query: types.CallbackQuery, state: FSMContext):
    amount = query.data.split('_')[-1]

    await state.update_data(amount=amount)
    data = await state.get_data()
    sep = '\n\t'
    text = f'''
Вы уверены, что хотите выдать дни?
Кому: {data['to_who'] if data['to_who'] != 'usernames' else sep + sep.join(data['usernames'])} 
Сколько: {data['amount']}
'''
    await state.set_state(GiveDaysStates.confirm)
    await query.message.edit_text(text=text, reply_markup=kbs.get_confirm_keyboard())
    await query.answer()


@router.callback_query(lambda query: query.data == 'confirm_yes', GiveDaysStates.confirm)
async def givedays_confirm_callback_handler(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    amount = data['amount']
    to_who = data['to_who']
    # another time verify that after all back buttons usernames does not contain something
    usernames = tuple(data.get('usernames', [])) if to_who == 'usernames' else ()
    await api.give_days(*usernames,
                        to_who=to_who,
                        amount=amount)

    await state.clear()
    await query.answer()
    await query.message.answer(f"SUBS: requesting subs for {amount} days to {to_who} : {usernames}")
    await query.message.delete()
