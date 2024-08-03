import hashlib
import pathlib
from contextlib import suppress

import aiofiles
import aiogram
from aiogram import types
from aiogram.exceptions import TelegramNetworkError, TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.utils.formatting import as_key_value, as_list, Bold, Text
from cryptography.fernet import Fernet

import telegram_bot.utils.keyboards as kbs


# Function to check if user is admin
# todo: remove return True IN PRODUCTION
async def is_user_admin(uid: int) -> bool:
    with open(pathlib.Path(__file__).parent.parent / '.admins', 'r', encoding='utf-8') as file:
        for admin_uid in file:
            if uid == int(admin_uid.strip()):
                return True
        return False


def get_settings_beautiful_list(settings: dict[str, str], active: str = None, header: str = '') -> Text:
    return as_list(
        Bold(header),
        *(as_key_value(('✅' if k == active else '') + k, v) for k, v in settings.items()),
        sep='\n'
    )


async def go_back(query: types.CallbackQuery, state: FSMContext, new_message=False, delete_old_message=False):
    with suppress(TelegramNetworkError):
        data = await state.get_data()
        previous_state = data.get('previous_state')
        previous_data = data.get('previous_data')
        previous_keyboard = data.get('previous_keyboard')
        previous_text = data.get('previous_text')

        # means that previous event was message and we dont need to create new message
        with suppress(TelegramBadRequest):
            if previous_keyboard is None:
                await send_main_menu(query.from_user.id, query.bot, query.message)

            elif new_message:
                if delete_old_message:
                    await query.message.delete()

                await query.message.answer(text=previous_text, reply_markup=previous_keyboard, parse_mode='HTML')
            else:
                await query.message.edit_text(text=previous_text, reply_markup=previous_keyboard, parse_mode='HTML')

        await state.set_state(previous_state)
        await state.update_data(previous_data)

        await query.answer()


async def send_main_menu(uid: str | int, bot: aiogram.Bot, message: Message = None):
    text = 'Привет, добро пожаловать в наш проект 0х1530. Это простой бот, позволяющий вам брать NFT через биды и всегда быть быстрее других.'
    if message:
        await message.edit_text(
            text=text,
            reply_markup=kbs.get_welcome_keyboard(is_admin=await is_user_admin(uid), uid=uid),
            parse_mode='HTML')
    else:
        await bot.send_message(
            uid,
            text=text,
            reply_markup=kbs.get_welcome_keyboard(is_admin=await is_user_admin(uid), uid=uid),
            parse_mode='HTML'
        )