import asyncio
from contextlib import suppress

from aiogram import Router, types, flags
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext

from handlers.create_unit.states import InitUnitStates
from utils import api

router = Router()


@router.message(InitUnitStates.uid)
async def create_unit_message_handler(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        m = await message.answer(text='UID должен быть целым числом')
        await asyncio.sleep(2)
        await m.delete()
        return

    try:
        c = await message.bot.get_chat(message.text)
        if c.type != 'private':
            raise TelegramBadRequest
    except TelegramBadRequest:
        m = await message.answer(text='Пользователя с данным UID не существует')
        await asyncio.sleep(2)
        await m.delete()
        return

    prev_message = (await state.get_data())['prev_message']
    status, text = await api.send_unit_command(message.text, 'create')

    match status:
        case 201:
            await message.answer(f'Юнит для пользователя {message.text} создан')
        case 500:
            await message.answer(f'Юнит для пользователя {message.text} не был создан из-за следующей ошибки:\n{text}')


    with suppress(TelegramBadRequest):
        await prev_message.delete()
        await message.delete()
    await state.clear()
