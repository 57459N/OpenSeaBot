from aiogram import Router, types
from aiogram.filters import CommandStart

from telegram_bot.utils.keyboards import get_no_sub_keyboard, get_welcome_keyboard
from telegram_bot.utils.api import is_user_subscribed
from telegram_bot.utils.misc import is_user_admin

router = Router()


@router.message(CommandStart())
async def command_start_handler(message: types.Message):
    user_id = message.from_user.id
    is_admin = await is_user_admin(user_id)
    is_sub = await is_user_subscribed(user_id)
    if (is_sub or is_admin) and True:
        text = ('Привет, добро пожаловать в наш проект 0х1530. '
                'Это простой бот, позволяющий вам брать NFT через биды и всегда быть быстрее других.')
        kb = get_welcome_keyboard(is_admin, user_id)
    else:
        text = 'Hello, you must sub before use this bot'
        kb = get_no_sub_keyboard()
    await message.answer(text=text, reply_markup=kb)
