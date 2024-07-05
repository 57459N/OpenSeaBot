from aiogram import Router, types, flags
from aiogram.fsm.context import FSMContext

from .states import BroadcastStates

router = Router()


@router.message(BroadcastStates.content)
@router.message(BroadcastStates.confirm)
@flags.backable()
async def message_broadcast_callback_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()

    if message.text:
        await state.update_data(text=message.text)
        if data['typee'] != 'photo':
            await state.update_data(typee='text')

    if message.photo:
        if message.caption:
            await state.update_data(typee='photo', photo=message.photo[-1], text=message.caption)
        else:
            await state.update_data(typee='photo', photo=message.photo[-1])

    messages_to_delete = data.get('messages_to_delete', [])
    messages_to_delete.append(message)

    await state.set_state(BroadcastStates.confirm)
    await state.update_data(messages_to_delete=messages_to_delete)
