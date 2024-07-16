import sys

import loguru

from aiogram import Router, flags, types, Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.fsm.context import FSMContext
from aiogram.types import InputFile, PhotoSize

from handlers.broadcast.states import BroadcastStates
from utils import api

import utils.keyboards as kbs

router = Router()


@router.callback_query(lambda query: query.data == 'broadcast')
@flags.backable()
async def broadcast_callback_handler(query: types.CallbackQuery, state: FSMContext):
    await state.set_state(BroadcastStates.to_who)
    await state.update_data(typee=None, photo=None, text=None)
    await query.message.edit_text('Выберите, кому вы хотите оповестить:',
                                  reply_markup=kbs.get_broadcast_keyboard())
    await query.answer()


@router.callback_query(lambda query: query.data in ['broadcast_all', 'broadcast_active', 'broadcast_inactive'],
                       BroadcastStates.to_who)
@flags.backable()
async def broadcast_who_callback_handler(query: types.CallbackQuery, state: FSMContext):
    to_who = query.data.split('_')[1]
    await state.update_data(to_who=to_who)
    await state.set_state(BroadcastStates.content)
    await query.message.edit_text('Введите текст для рассылки, также можете прислать изображение:',
                                  reply_markup=kbs.get_broadcast_content_keyboard())
    await query.answer()


@router.callback_query(lambda query: query.data == 'broadcast_content_ready', BroadcastStates.confirm)
async def broadcast_confirm_callback_handler(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    to_who = data['to_who']
    broadcast_text = data['text']
    photo = data['photo']
    typee = data['typee']

    messages_to_delete = data.get('messages_to_delete', [])
    for m in messages_to_delete:
        try:
            await m.delete()
        except TelegramBadRequest:
            pass

    uids = await api.get_user_ids(to_who)
    await state.update_data(uids=uids)

    text = f'''
\t{broadcast_text if broadcast_text else ' '}

Вы уверены, что хотите оповестить?
Кого: {to_who.capitalize()}
Охват: {len(uids)} пользователей'''

    await send(query.from_user.id, query.bot, typee, text, photo, reply_markup=kbs.get_broadcast_confirm_keyboard())
    await query.answer()
    await query.message.delete()


@router.callback_query(lambda query: query.data == 'broadcast_confirm_yes', BroadcastStates.confirm)
async def broadcast_action_callback_handler(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    uids = set(data['uids'])
    broadcast_text = data['text']
    photo = data['photo']
    typee = data['typee']

    await state.clear()
    await query.answer()
    await query.message.delete()
    new_message = await query.message.answer(f'Оповещение начато.')

    successful_count = 0
    for user in uids:
        is_successful = int(await send(user, query.bot, typee, broadcast_text, photo))
        successful_count += int(is_successful)
        loguru.logger.info(f'BROADCAST: user:{user}, success:{is_successful}')

    await new_message.edit_text(
        f'Оповещение завершено.\n'
        f'Доставлено {successful_count}/{len(uids)} ({successful_count / len(uids) * 100:.1f}%) сообщений.')


async def send(user_id: int | str, bot: Bot, typee: str, text: str, photo: PhotoSize = None,
               reply_markup: types.InlineKeyboardMarkup = None) -> bool:
    try:
        if typee == 'photo':
            await bot.send_photo(chat_id=user_id, caption=text, photo=photo.file_id, reply_markup=reply_markup)
        elif typee == 'text':
            await bot.send_message(chat_id=user_id, text=text, reply_markup=reply_markup)
        return True
    except (TelegramBadRequest, TelegramForbiddenError) as e:
        loguru.logger.warning(f'BROADCAST: user:{user_id}: {e.label}: {e.message}')
    return False
