import asyncio
import sys

import loguru

from aiogram import Router, flags, types, Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.fsm.context import FSMContext
from aiogram.types import InputFile, PhotoSize

import config
from handlers.collections.states import CollectionsStates
from telegram_bot.utils import api

import telegram_bot.utils.keyboards as kbs
from utils.misc import send_main_menu

router = Router()


@router.callback_query(lambda callback_query: callback_query.data == 'collections_menu')
@flags.backable()
async def collections_menu_callback_handler(query: types.CallbackQuery, state: FSMContext):
    await query.message.edit_text(
        text='Collections menu', reply_markup=kbs.get_collections_menu_keyboard())
    await query.answer()


@router.callback_query(lambda callback_query: callback_query.data == 'collections_set')
@flags.backable()
async def collections_set_list_callback_handler(query: types.CallbackQuery, state: FSMContext):
    await state.set_state(CollectionsStates.set_list)
    await state.update_data(collections=None)
    await query.message.edit_text(
        text='Enter your collections to add:'
             '\tEvery new collection name must start with the new-line',
        reply_markup=kbs.get_collections_setting_keyboard())
    await query.answer()


@router.callback_query(lambda query: query.data == 'collections_set_finish', CollectionsStates.set_list)
async def collections_set_finish_callback_handler(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    collections: list[str] | None = data.get('collections', None)

    if collections is None or len(collections) == 0:
        await query.answer('Add at least one collection', show_alert=True)
        return

    uid = query.from_user.id
    status, text = await api.set_collections(collections, uid)

    if status == 200:
        await query.message.edit_text('✅ Collections set successfully')
        await send_main_menu(uid, query.bot)
    else:
        await query.bot.send_message(config.SUPPORT_UID,
                                     text=f'<b>Error while setting collections on user</b> <code>{uid}</code>:\n{status}:{text}',
                                     reply_markup=kbs.get_delete_keyboard())
        await send_main_menu(uid, query.bot, query.message)
        await query.message.answer(text='Something went wrong. Try again later or contact support',
                                   reply_markup=kbs.get_support_keyboard())
    await state.clear()
    await query.answer()
