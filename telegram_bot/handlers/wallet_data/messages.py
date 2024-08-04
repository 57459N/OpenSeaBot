import asyncio

import web3
from aiogram import Router, types, flags
from aiogram.fsm.context import FSMContext
from aiogram.utils.formatting import Bold, Code

from telegram_bot.handlers.wallet_data.states import WalletDataStates
from telegram_bot.utils import keyboards as kbs

router = Router()


@router.message(WalletDataStates.private_key)
async def private_key_message_handler(message: types.Message, state: FSMContext):
    pk = message.text.strip()
    data = await state.get_data()
    messages_to_delete = data.get('messages_to_delete', [])

    # validating pk
    try:
        acc = web3.Account.from_key(pk)
    except Exception as e:
        m = await message.answer("Invalid private's key format. Please try again.")
        messages_to_delete.append(message)
        await state.update_data(messages_to_delete=messages_to_delete)

        await asyncio.sleep(3)
        await m.delete()
        return

    await state.update_data(private_key=pk)
    await state.set_state(WalletDataStates.confirmation)

    await message.delete()
    for m in messages_to_delete:
        await m.delete()

    prev_message = (await state.get_data())['prev_message']
    await prev_message.edit_text(
        f'<b>Are you sure you want to change your wallet details to the following?</b>\n\n'
        f'❗️ <b><i>The last private key will no longer be stored on our servers and may be lost</i></b>'
        f'\n\nNew private key: {Code(pk).as_html()}'
        , reply_markup=kbs.get_confirm_keyboard())
