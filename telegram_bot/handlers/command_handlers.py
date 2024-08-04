from aiogram import Router, types
from aiogram.filters import CommandStart

from telegram_bot.utils.keyboards import get_no_sub_keyboard, get_welcome_keyboard
from telegram_bot.utils.api import is_user_subscribed
from telegram_bot.utils.misc import is_user_admin, send_main_menu

router = Router()


@router.message(CommandStart())
async def command_start_handler(message: types.Message):
    user_id = message.from_user.id
    is_admin = await is_user_admin(user_id)
    is_sub = await is_user_subscribed(user_id)
    if (is_sub or is_admin) and True:
        await send_main_menu(user_id, message.bot)
    else:
        await message.answer(text='<b>Before using our bot, you are required to subscribe to our resources</b>', reply_markup=get_no_sub_keyboard())
