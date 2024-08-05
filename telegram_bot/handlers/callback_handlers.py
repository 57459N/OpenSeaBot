import asyncio
from contextlib import suppress
from datetime import datetime, timedelta

from aiogram.exceptions import TelegramBadRequest
from aiogram.utils.formatting import Code, Bold
from aiogram import Router, types, F, flags
from aiogram.fsm.context import FSMContext

import config
from telegram_bot.handlers.callbacks_data import PaginationCallback, SelectCallback
from telegram_bot.middlwares.backable_query_middleware import BackableMiddleware
from telegram_bot.middlwares.sub_active_middleware import SubActiveMiddleware
from telegram_bot.utils import api
from telegram_bot.utils.misc import go_back, send_main_menu

import telegram_bot.utils.keyboards as kbs

router = Router()
router.callback_query.middleware(BackableMiddleware())
router.callback_query.middleware(SubActiveMiddleware())


@router.callback_query(PaginationCallback.filter(F.action == "paginate"))
async def paginate_callback_handler(query: types.CallbackQuery, callback_data: PaginationCallback, state: FSMContext):
    data = await state.get_data()
    await query.message.edit_reply_markup(
        reply_markup=kbs.get_choose_keyboard(options=data.get("options", []),
                                             selected=data.get("selected_options", set()),
                                             page=callback_data.page))
    await query.answer()


@router.callback_query(SelectCallback.filter())
async def select_callback_handler(query: types.CallbackQuery, callback_data: SelectCallback, state: FSMContext):
    option = callback_data.option

    data = await state.get_data()
    selected_options = data.get('selected_options', set())

    if option in selected_options:
        selected_options.remove(option)
    else:
        selected_options.add(option)

    await state.update_data(selected_options=selected_options)
    await query.message.edit_reply_markup(reply_markup=kbs.get_choose_keyboard(options=data.get('options'),
                                                                               selected=selected_options,
                                                                               page=callback_data.page))
    await query.answer()


@router.callback_query(lambda query: query.data == 'back')
async def universal_back_callback_handler(query: types.CallbackQuery, state: FSMContext):
    await go_back(query, state)


@router.callback_query(lambda query: query.data == 'delete_message')
async def noop_callback_handler(query: types.CallbackQuery, state: FSMContext):
    # await state.clear()
    await query.message.delete()
    await query.answer()


# Welcome menu #

@router.callback_query(lambda query: query.data == 'sub_info')
@flags.backable()
@router.callback_query(lambda query: query.data == 'sub_info_reload')
async def sub_info_callback_handler(query: types.CallbackQuery):
    if sub_info := await api.get_user_subscription_info_by_id(query.from_user.id):
        status = sub_info.get('status', 'Inactive')
        days_left = sub_info.get('days_left', 0)
        own_balance = sub_info.get('balance', 0)
        bot_wallet = sub_info.get('bot_wallet', None)
        bot_balance_eth = sub_info.get('bot_balance_eth', None)
        bot_balance_weth = sub_info.get('bot_balance_weth', None)

    text = f'''
<b>📃 In this section you able to:</b>
<blockquote><i>- renew your subscription
- get information about the bot's balance
- get or change a your bot's private key</i></blockquote>
'''
    if (act_cost := sub_info.get('activation_cost', None)) and status in {'Inactive', 'Deactivated', 'Not active'}:
        text += f"\n<b>To activate your subscription, your balance must be at least {act_cost}</b>\n"

    text += f'''
<b>Subscription Status:</b> {status}
<b>Subscription days left:</b> {days_left}
<b>Balance:</b> {own_balance}
'''

    if bot_wallet:
        text += f'''
<b>Balance ETH:</b> {bot_balance_eth}
<b>Balance WETH:</b> {bot_balance_weth}
<b>Work address:</b> {Code(bot_wallet).as_html()}
'''
    else:
        text += "\n<i><b>Now your account has not been created. You don't have a working wallet yet, you need to pay for a subscription to get access to the bot</b></i>"

    with suppress(TelegramBadRequest):
        await query.message.edit_text(text=text, reply_markup=kbs.get_sub_info_keyboard(), parse_mode='HTML')
    await query.answer()


@router.callback_query(lambda query: query.data == 'get_user_tgid')
async def extend_sub_callback_handler(query: types.CallbackQuery):
    await query.message.answer(**Code(str(query.from_user.id)).as_kwargs())
    await query.answer()


@router.callback_query(lambda query: query.data == 'sub_manage')
@flags.sub_active()
@flags.backable()
async def extend_sub_callback_handler(query: types.CallbackQuery, state: FSMContext):
    text = '''
<b>🔧 Control Panel</b>

<i>- In the "FAQ" section you can read all the information about running and managing the bot 
- In the "Opensea bidder" section you can change bot settings, start or stop the current working session</i>'''

    await query.message.edit_text(text=text, reply_markup=kbs.get_instruments_keyboard())
    await query.answer()


@router.callback_query(lambda query: query.data == 'main_menu')
async def main_menu_callback_handler(query: types.CallbackQuery):
    await send_main_menu(query.from_user.id, query.bot, query.message)


# Admin menu #
@router.callback_query(lambda query: query.data == 'admin_menu')
async def admin_menu_callback_handler(query: types.CallbackQuery):
    await query.message.answer(text='Админ меню', reply_markup=kbs.get_admin_menu_keyboard())
    await query.answer()


@router.callback_query(lambda query: query.data == 'dev')
async def dev_menu_callback_handler(query: types.CallbackQuery):
    await query.message.answer(text='Dev', reply_markup=kbs.get_dev_keyboard())
    await query.answer()
