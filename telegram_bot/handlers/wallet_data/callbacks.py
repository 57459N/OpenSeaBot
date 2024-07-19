import sys

import loguru
import os

from aiogram import Router, flags, types, Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.fsm.context import FSMContext
from aiogram.utils.formatting import Code, Bold

import config
import misc
import utils.keyboards as kbs
from handlers.wallet_data.states import WalletDataStates
from utils import api
from utils.misc import decrypt_private_key

router = Router()


@router.callback_query(lambda query: query.data == 'wallet_data_menu')
@flags.backable()
async def wallet_data_menu_callback_handler(query: types.CallbackQuery, state: FSMContext):
    text = 'Меню кошелька, при помощи которого будет вестись торговля NFT'
    kb = kbs.get_wallet_data_menu_keyboard()
    await query.message.edit_text(text=text, reply_markup=kb)
    await query.answer()


@router.callback_query(lambda query: query.data == 'wallet_data_get_private')
async def get_wallet_data_callback_handler(query: types.CallbackQuery, state: FSMContext):
    key = await api.send_unit_command(query.from_user.id, 'get_private_key')
    decrypted = await decrypt_private_key(key, config.BOT_API_TOKEN)
    await query.message.answer(
        f'В целях {Bold("безопасности").as_html()} рекомендуется {Bold("удалить данное сообщение").as_html()}'
        f' после копирования ключа.'
        f'\n\nПриватный ключ кошелька:\n{Code(decrypted).as_html()}'
        , parse_mode='HTML')
    await query.answer()


@router.callback_query(lambda query: query.data == 'wallet_data_set')
async def set_wallet_address_callback_handler(query: types.CallbackQuery, state: FSMContext):
    await state.set_state(WalletDataStates.address)
    m = await query.message.answer(
        'Введите адрес кошелька. Данный адрес используется для получения баланса кошелька для отображения в профиле.'
        '\n\nДанный пункт можно пропустить. Данные о балансе показываться не будут.'
        , reply_markup=kbs.get_skip_keyboard('wallet_data_set_address_skip'))
    await state.update_data(prev_message=m)
    await query.answer()


@router.callback_query(lambda query: query.data == 'wallet_data_set_address_skip')
async def skip_wallet_address_callback_handler(query: types.CallbackQuery, state: FSMContext):
    await state.update_data(address=None)
    await state.set_state(WalletDataStates.private_key)
    await query.message.edit_text(
        'Введите приватный ключ кошелька. Данный ключ будет использоваться для торговли является обязательным.'
        , reply_markup=kbs.get_delete_keyboard())
    await query.answer()


@router.callback_query(lambda query: query.data == 'confirm_yes', WalletDataStates.confirmation)
async def set_wallet_data_callback_handler(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    address = data['address']
    private_key = data['private_key']
    encrypted = await misc.encrypt_private_key(private_key, config.BOT_API_TOKEN)

    await api.send_unit_command(query.from_user.id, 'set_wallet_data',
                                data={'address': address, 'private_key': encrypted})
    prev_message = data['prev_message']
    await prev_message.delete()
