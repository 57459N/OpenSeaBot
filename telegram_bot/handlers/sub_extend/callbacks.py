import asyncio
from datetime import datetime, timedelta

from aiogram import Router, flags, types
from aiogram.fsm.context import FSMContext
from aiogram.utils.formatting import Code

import config
from telegram_bot.handlers.sub_extend.states import SubExtendStates
from telegram_bot.utils import api
import telegram_bot.utils.keyboards as kbs

router = Router()


@router.callback_query(lambda query: query.data == 'sub_extend')
@flags.backable()
async def extend_sub_callback_handler(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    wallet = data.get('wallet', None)

    await query.answer()

    await state.set_state(SubExtendStates.showing_wallet)
    while await edit_message_with_wallet_info(query, state, wallet):
        await asyncio.sleep(1)


@router.callback_query(lambda query: query.data == 'sub_extend_generate')
async def extend_sub_generate_callback_handler(query: types.CallbackQuery, state: FSMContext):
    uid = query.from_user.id

    wallet_id = await api.get_wallet_to_extend_sub(uid)
    wallet = {
        'id': wallet_id,
        'expires': datetime.now() + timedelta(seconds=config.WALLET_EXPIRE_SECONDS),
    }
    await state.update_data(wallet=wallet)

    await query.answer()

    await state.set_state(SubExtendStates.showing_wallet)
    while await edit_message_with_wallet_info(query, state, wallet):
        await asyncio.sleep(1)
    await state.set_state(None)


async def edit_message_with_wallet_info(query: types.CallbackQuery, state: FSMContext, wallet: dict | None):
    if wallet is None:
        text = '''
Сгенерируйте уникальный кошелек для транзакции.

Данный кошелек будет активен в течении <b>30 минут</b>, после чего нужно будет необходимо сгенерировать новый. 
'''
        kb = kbs.get_sub_extend_generate_keyboard()
        ret = False
    elif datetime.now() > wallet['expires']:
        text = f'Кошелек устарел. Необходимо сгенерировать новый.\n\nКошелек будет активен в течении <b>30 минут</b>, после чего нужно будет необходимо сгенерировать новый. '
        kb = kbs.get_sub_extend_generate_keyboard()
        ret = False
    else:
        s = (wallet['expires'] - datetime.now()).seconds
        t = f'{s // 60} мин.' if s > 60 else f'{s} сек.'

        w = Code(str(wallet['id'])).as_html()

        text = f'''
{w}\n
❗️Сгенерированный кошелек доступен в течении {t}❗'''
        kb = kbs.get_sub_extend_to_main_menu_keyboard()
        ret = True

    if wallet is not None and await state.get_state() != SubExtendStates.showing_wallet:
        return False

    await query.message.edit_text(text=text, reply_markup=kb, parse_mode='HTML')

    return ret
