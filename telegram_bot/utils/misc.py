import hashlib
from contextlib import suppress

import aiofiles
from aiogram import types
from aiogram.exceptions import TelegramNetworkError, TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.utils.formatting import as_key_value, as_list, Bold, Text
from cryptography.fernet import Fernet


# Function to check if user is admin
# todo: remove return True IN PRODUCTION
async def is_user_admin(uid: int) -> bool:
    return True
    async with aiofiles.open('.admins', 'r', encoding='utf-8') as file:
        async for admin_uid in file:
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
                await query.message.delete()
            elif new_message:
                if delete_old_message:
                    await query.message.delete()

                await query.message.answer(text=previous_text, reply_markup=previous_keyboard)
            else:
                await query.message.edit_text(text=previous_text, reply_markup=previous_keyboard)

        await state.set_state(previous_state)
        await state.update_data(previous_data)

        await query.answer()


async def decrypt_secret_key(secret: str, password: str) -> str:
    key = hashlib.sha256(password.encode()).hexdigest()[:43] + "="
    return Fernet(key).decrypt(secret).decode()

