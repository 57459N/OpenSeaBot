import asyncio
import loguru

from contextlib import suppress
from datetime import datetime

from aiogram import Router, flags, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.utils.formatting import Code

from middlwares.backable_query_middleware import BackableMiddleware
from payments.system import Wallet, manager as payments_manager
from telegram_bot.utils import api

import config
import telegram_bot.utils.keyboards as kbs
from utils.misc import send_main_menu

router = Router()
router.callback_query.middleware(BackableMiddleware())


@router.callback_query(lambda query: query.data == 'sub_extend')
@flags.backable()
async def sub_extend_callback_handler(query: types.CallbackQuery, state: FSMContext):
    await edit_with_wallet_info(query, state)


@router.callback_query(lambda query: query.data == 'sub_extend_generate')
async def sub_extend_generate_wallet_callback_handler(query: types.CallbackQuery, state: FSMContext):
    uid = query.from_user.id
    wallet = await payments_manager.get_temporary_wallet(uid)
    loguru.logger.info(f'SUB_EXTEND: generating wallet for {uid}')

    await state.update_data(wallet=wallet)
    await query.answer()

    async def handle_payment():
        # todo: UNCOMMENT WITH REAL PAYMENT SYSTEM
        response = await payments_manager.handle_payment(wallet)
        if response:
            paid_amount = response["balance"]

            wallet.paid = True
            if await api.increase_user_balance(uid, paid_amount):
                text = f'<b>🎉 {paid_amount} usd has been credited to the balance. Thank you for payment</b>'
                kb = kbs.get_delete_keyboard()

                await query.bot.send_message(config.SUPPORT_UID,
                                             f'🦣 Мамонт оплатил @{query.from_user.username}:<code>{query.from_user.id}</code> профит {paid_amount}.',
                                             parse_mode='HTML')
                loguru.logger.info(f'SUB_EXTEND: payment got {paid_amount} from user {uid}')
            else:
                text = '<i>🤷‍♂️ Error when refilling balance. Notify the administrator about the issue</i>'
                kb = kbs.get_support_keyboard()

                loguru.logger.error(f'SUB_EXTEND: payment error for user {uid}')

            try:
                await query.message.edit_text(text=text, reply_markup=kb)
            except TelegramBadRequest:
                await query.message.answer(text=text, reply_markup=kb)

            await send_main_menu(query.from_user.id, query.bot)

    asyncio.create_task(handle_payment())
    await edit_with_wallet_info(query, state)


async def edit_with_wallet_info(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    wallet: Wallet | None = data.get("wallet", None)
    if wallet:
        s = (wallet.expires - datetime.now()).seconds
        t = f'{s // 60} min.' if s > 60 else f'{s} sec.'
        w = Code(str(wallet.address)).as_html()

        with suppress(TelegramBadRequest):
            await query.message.edit_text(
                text=f'''
<b>❗️The payment address will be available in next {t}❗️

Send your USDT or USDC in this available nets:</b>
<i>- Ethereum
- Arbitrum
- Optimism
- Binance Smart Chain </i>

Temporary wallet: {w}

After that the bot itself will check that you made the payment and will inform you when the funds will be credited to your balance. You do not need to send any payment confirmation to the bot, it will see the receipt on its own

<b>Important note:</b> <i>If you make a payment after the end of the wallet lease, the administration will not be able to return the funds to you and they may be lost</i>
''',
                reply_markup=kbs.get_just_back_button_keyboard()
            )
    else:
        text = '''
<b>🧞‍♀️ Generate a unique wallet for your transaction.</b>

<i>💡This wallet will be valid for the next 30 minutes, after which it will be necessary to generate a new wallet.</i>'''
        kb = kbs.get_sub_extend_generate_keyboard()
        await query.message.edit_text(text=text, reply_markup=kb)
