import sys

import loguru
import os

from aiogram import Router, flags, types, Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.fsm.context import FSMContext
from aiogram.types import InputFile, PhotoSize
from aiogram.utils.formatting import Code, Bold

import config
import telegram_bot.utils.keyboards as kbs
from telegram_bot.utils import api
from encryption.system import decrypt_private_key

router = Router()

