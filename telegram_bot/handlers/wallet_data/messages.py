from aiogram import Router, types, flags
from aiogram.fsm.context import FSMContext
from aiogram.utils.formatting import Bold, Code

from telegram_bot.handlers.wallet_data.states import WalletDataStates
from telegram_bot.utils import keyboards as kbs

router = Router()


@router.message(WalletDataStates.private_key)
async def private_key_message_handler(message: types.Message, state: FSMContext):
    pk = message.text.strip()
    await state.update_data(private_key=pk)
    await state.set_state(WalletDataStates.confirmation)
    await message.delete()
    prev_message = (await state.get_data())['prev_message']
    await prev_message.edit_text(
        f'<b>Are you sure you want to change your wallet details to the following?</b>\n\n'
        f'❗️ <b><i>The last private key will no longer be stored on our servers and may be lost</i></b>'
        f'\n\nNew private key: {Code(pk).as_html()}'
        , reply_markup=kbs.get_confirm_keyboard())
