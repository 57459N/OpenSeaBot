import asyncio
import loguru

from asyncio import CancelledError
from contextlib import suppress
from datetime import datetime

from aiogram import Router, flags, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.utils.formatting import Code
from payments import Wallet, manager as payments_manager
from telegram_bot.handlers.sub_extend.states import SubExtendStates
from telegram_bot.utils import api

import config
import telegram_bot.utils.keyboards as kbs

router = Router()


@router.callback_query(lambda query: query.data == 'sub_extend')
@flags.backable()
async def sub_extend_callback_handler(query: types.CallbackQuery, state: FSMContext):
    await state.set_state(SubExtendStates.showing_wallet)
    await query.answer()
    data = await state.get_data()

    if wallet_message := data.get('generate_wallet_message', None):
        with suppress(TelegramBadRequest):
            await wallet_message.delete()
            await state.update_data(generate_wallet_message=None)

    if task := data.get('wallet_message_task', None):
        task.cancel()
        await state.update_data(wallet_message_task=None)
        with suppress(CancelledError):
            await task

    await (state.update_data(wallet_message_task=asyncio.create_task(edit_with_wallet_info(query, state))))


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
        else:
            paid_amount = 0

        if paid_amount != 0:
            wallet.paid = True
            if await api.increase_user_balance(uid, paid_amount):
                text = f'На баланс зачислено {paid_amount}. Благодарим за оплату'
                kb = kbs.get_delete_keyboard()
                await query.bot.send_message(config.SUPPORT_UID,
                                             f'✅ Пользователь @{query.from_user.username}:<code>{query.from_user.id}</code> оплатил {paid_amount}.',
                                             parse_mode='HTML')
                loguru.logger.info(f'SUB_EXTEND: payment got {paid_amount} from user {uid}')
            else:
                text = 'Ошибка при пополнении баланса. Сообщите администратору'
                kb = kbs.get_support_keyboard()
                loguru.logger.error(f'SUB_EXTEND: payment error for user {uid}')
            try:
                await query.message.edit_text(text=text, reply_markup=kb)
            except TelegramBadRequest:
                data = await state.get_data()
                if m := data.get('generate_wallet_message', None):
                    try:
                        await m.edit_text(text=text, reply_markup=kb)
                    except TelegramBadRequest:
                        await query.message.answer(text=text, reply_markup=kb)

    asyncio.create_task(handle_payment())
    await edit_with_wallet_info(query, state, answer=False)
    await state.update_data(wallet=None)


async def edit_with_wallet_info(query: types.CallbackQuery, state: FSMContext, answer=True):
    data = await state.get_data()
    wallet: Wallet | None = data.get("wallet", None)
    if answer:
        message = await query.message.answer('1')
        await state.update_data(generate_wallet_message=message)
    else:
        message = query.message

    if wallet is None:
        try:
            text = '''
Сгенерируйте уникальный кошелек для транзакции.\n        
Данный кошелек будет активен в течении <b>30 минут</b>, после чего нужно будет необходимо сгенерировать новый.
                '''
            kb = kbs.get_sub_extend_generate_keyboard()
            await message.edit_text(text=text, reply_markup=kb)
        except TelegramBadRequest:
            pass
        return

    # Если кошелек сгенерирован, показать информацию о нем и ждать оплаты
    while wallet:
        s = (wallet.expires - datetime.now()).seconds
        t = f'{s // 60} мин.' if s > 60 else f'{s} сек.'
        w = Code(str(wallet.address)).as_html()

        with suppress(TelegramBadRequest):
            await message.edit_text(text=f'{w}\n\n❗Данный кошелек будет доступен в течении {t}❗',
                                    reply_markup=kbs.get_delete_keyboard())

        await asyncio.sleep((s % 60) + 1 if s > 60 else 1)

        wallet = (await state.get_data()).get('wallet', None)

    if not wallet.paid:
        text = ('Кошелек больше не действителен. Пожалуйста сгенерируйте новый кошелек для оплаты.'
                '\n\nДанный кошелек будет активен в течении <b>30 минут</b>, после чего нужно будет необходимо сгенерировать новый.')
        kb = kbs.get_sub_extend_generate_keyboard()
        await state.update_data({"wallet": None})
        with suppress(TelegramBadRequest):
            await message.edit_text(text=text, reply_markup=kb)
