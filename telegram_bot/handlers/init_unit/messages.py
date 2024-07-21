import asyncio
from contextlib import suppress

from aiogram import Router, types, flags
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext

from telegram_bot.handlers.create_unit.states import InitUnitStates
from telegram_bot.utils import api

router = Router()
