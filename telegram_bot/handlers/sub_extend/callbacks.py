import asyncio
import dataclasses
import logging
from asyncio import CancelledError
from contextlib import suppress
from datetime import datetime, timedelta

from aiogram import Router, flags, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.utils.formatting import Code

from telegram_bot import config
from telegram_bot.handlers.sub_extend.states import SubExtendStates
from telegram_bot.utils import api, payments
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
    # todo: UNCOMMENT WITH REAL PAYMENT SYSTEM
    # account = await payments.generate_account()
    # wallet = Wallet(address=account['address'], expires=datetime.now() + timedelta(seconds=180))
    logging.info(f'SUB_EXTEND: generating wallet for {uid}')
    # todo: change address to address from account
    wallet = Wallet(address=('TEST WALLET ACC ADDRESS'))

    await state.update_data(wallet=wallet)
    await query.answer()

    async def handle_payment():

        paid_amount = 259
        await asyncio.sleep(5)

        # todo: UNCOMMENT WITH REAL PAYMENT SYSTEM
        # response = await payments.check_payment_handler(
        #     config={
        #         "ethereum": {
        #             "rpc": "https://1rpc.io/eth",
        #             "tokens": [
        #                 "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        #                 "0xdAC17F958D2ee523a2206206994597C13D831ec7"
        #             ]
        #         }
        #     },
        #     timeout=config.WALLET_EXPIRE_SECONDS,
        #     _address=account["address"]
        # )
        # if response:
        #    paid_amount = response["balance"]

        if paid_amount != 0:
            wallet.paid = True
            if await api.increase_user_balance(uid, paid_amount, query.bot.token):
                text = f'На баланс зачислено {paid_amount}. Благодарим за оплату'
                kb = kbs.get_delete_keyboard()
                logging.info(f'SUB_EXTEND: payment got {paid_amount} from user {uid}')
            else:
                text = 'Ошибка при пополнении баланса. Сообщите администратору'
                kb = kbs.get_support_keyboard()
                logging.error(f'SUB_EXTEND: payment error for user {uid}')
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


@dataclasses.dataclass
class Wallet:
    address: str
    expires: datetime
    paid: bool

    def __init__(self, address: str, expires: datetime = None, paid: bool = False):
        self.address = address
        self.paid = paid
        if expires is None:
            self.expires = datetime.now() + timedelta(seconds=config.WALLET_EXPIRE_SECONDS)
        else:
            self.expires = expires

    def __bool__(self):
        return not self.paid and self.expires > datetime.now()


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
