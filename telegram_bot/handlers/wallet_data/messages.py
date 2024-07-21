from aiogram import Router, types, flags
from aiogram.fsm.context import FSMContext
from aiogram.utils.formatting import Bold, Code

from telegram_bot.handlers.wallet_data.states import WalletDataStates
from telegram_bot.utils import keyboards as kbs

router = Router()


@router.message(WalletDataStates.address)
async def address_message_handler(message: types.Message, state: FSMContext):
    await state.update_data(address=message.text.strip())
    await state.set_state(WalletDataStates.private_key)
    await message.delete()
    prev_message = (await state.get_data())['prev_message']
    await prev_message.edit_text(
        'Введите приватный ключ кошелька. Данный ключ будет использоваться для торговли и является обязательным.'
        , reply_markup=kbs.get_just_back_button_keyboard())


@router.message(WalletDataStates.private_key)
async def private_key_message_handler(message: types.Message, state: FSMContext):
    pk = message.text.strip()
    await state.update_data(private_key=pk)
    await state.set_state(WalletDataStates.confirmation)
    await message.delete()
    prev_message = (await state.get_data())['prev_message']
    data = await state.get_data()
    await prev_message.edit_text(
        f'Вы уверены, что хотите изменить данные кошелька на следующие?'
        f'\n\nАдрес: {Code(data["address"]).as_html()}'
        f'\nСекретный ключ:\n{Code(pk).as_html()}'
        , reply_markup=kbs.get_confirm_keyboard())
