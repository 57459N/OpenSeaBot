import asyncio

from aiogram import types, flags, Router
from aiogram.fsm.context import FSMContext
from handlers.givedays.states import GiveDaysStates
from middlwares.backable_query_middleware import BackableMiddleware
from utils import keyboards as kbs

# from . import router

router = Router()


@router.message(GiveDaysStates.amount)
@flags.backable()
async def amount_message_handler(message: types.Message, state: FSMContext):
    if message.text.strip().isdecimal():
        amount = int(message.text.strip())

        await state.update_data(amount=amount)
        data = await state.get_data()
        sep = '\n\t'
        text = f'''
Вы уверены, что хотите выдать дни?
Кому: {data['to_who'] if data['to_who'] != 'usernames' else sep + sep.join(data['usernames'])} 
Сколько: {data['amount']}
'''
        await state.set_state(GiveDaysStates.confirm)

        await message.delete()
        await state.update_data(previous_keyboard=kbs.get_givedays_amount_keyboard(),
                                previous_text='Введите или выберите количество дней, которое нужно выдать')

        await data['prev_message'].edit_text(text=text, reply_markup=kbs.get_confirm_keyboard())
    else:
        error_message = await message.answer(text='Пожалуйста введите число.')
        await asyncio.sleep(1)
        await error_message.delete()
        await message.delete()


@router.message(GiveDaysStates.usernames)
async def amount_message_handler(message: types.Message, state: FSMContext):
    users = set(map(lambda x: x.strip('@, '), message.text.split('\n')))

    data = await state.get_data()
    username_to_id = data['username_to_id']

    found, not_found = set(), set()

    for u in users:
        (not_found, found)[u in username_to_id].add(u)

    messages_to_delete = data.get('messages_to_delete')
    if messages_to_delete is None: messages_to_delete = []

    if len(not_found):
        user_list = '\n\t'.join(not_found)
        m = await message.answer(f'Следующие пользователи не были добавлены, так как не найдены:\n\t{user_list}')
        messages_to_delete.append(m)
    messages_to_delete.append(message)

    new_users = found.union(data.get('usernames', set()))

    await state.update_data(usernames=new_users, messages_to_delete=messages_to_delete)
