from aiogram.fsm.state import StatesGroup, State


class BroadcastStates(StatesGroup):
    to_who = State()
    content = State()
    confirm = State()