import asyncio
from contextlib import suppress

from aiogram import Router, types, flags
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext

from handlers.create_unit.states import InitUnitStates
from utils import api

router = Router()
