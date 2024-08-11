import asyncio
import sys

import loguru
import os

from aiogram import Router, flags, types, Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.fsm.context import FSMContext
from aiogram.utils.formatting import Code, Bold

import config
import telegram_bot.utils.keyboards as kbs
from telegram_bot.handlers.wallet_data.states import WalletDataStates
from telegram_bot.utils import api
from telegram_bot.middlwares.backable_query_middleware import BackableMiddleware
from encryption.system import decrypt_private_key, encrypt_private_key
from utils.misc import send_main_menu

router = Router()
router.callback_query.middleware(BackableMiddleware())


@router.callback_query(lambda query: query.data == 'wallet_data_menu')
@flags.backable()
async def wallet_data_menu_callback_handler(query: types.CallbackQuery):
    text = '''
<b>📃 In this section you able to:</b>
<i>- get your current private key
- change private key to your own</i>
'''
    kb = kbs.get_wallet_data_menu_keyboard()
    await query.message.edit_text(text=text, reply_markup=kb)
    await query.answer()


@router.callback_query(lambda query: query.data == 'wallet_data_get_private')
async def get_wallet_data_callback_handler(query: types.CallbackQuery, state: FSMContext):
    key = await api.send_instrument_command(query.from_user.id, 'unit', 'get_private_key')

    if isinstance(key, tuple):
        await query.answer("😔 <b>Your unit has not been created, contact support.</b>", show_alert=True)
        return

    decrypted = await decrypt_private_key(key, config.BOT_API_TOKEN)
    await query.message.answer(
        f'''
<b>For security reasons, we recommended to delete this message after copying the key.</b>

<b>Private key:</b> {Code(decrypted).as_html()}
'''
        , parse_mode='HTML'
        , reply_markup=kbs.get_delete_keyboard())
    await query.answer()


@router.callback_query(lambda query: query.data == 'wallet_data_set')
@flags.backable()
async def skip_wallet_address_callback_handler(query: types.CallbackQuery, state: FSMContext):
    await state.set_state(WalletDataStates.private_key)
    await state.update_data(prev_message=query.message)
    await query.message.edit_text(
        '''
<b>Enter the private key of the wallet</b>

💡 <i>This key will be used for bidding on Opensea and Opensea Pro.</i>
'''
        , reply_markup=kbs.get_just_back_button_keyboard())
    await query.answer()


@router.callback_query(lambda query: query.data == 'confirm_yes', WalletDataStates.confirmation)
async def set_wallet_data_callback_handler(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    private_key = data['private_key']
    encrypted = (await encrypt_private_key(private_key, config.BOT_API_TOKEN)).decode()

    status, text = await api.send_wallet_data(uid=query.from_user.id,
                                              data={'private_key': encrypted})

    prev_message = data['prev_message']
    match status:
        case 200:
            await prev_message.edit_text('✅ <b>Your key has been set.</b>', parse_mode='HTML')
            await asyncio.sleep(0.2)
            await send_main_menu(query.from_user.id, query.message.bot)
        case 404:
            await query.answer('😔 <b>Your key has not been set, contact support.</b>', show_alert=True)

    await state.clear()


@router.callback_query(lambda query: query.data == 'confirm_no', WalletDataStates.confirmation)
async def skip_wallet_address_callback_handler(query: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await send_main_menu(query.from_user.id, query.message.bot, query.message)
