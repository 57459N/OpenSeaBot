from aiogram.fsm.state import StatesGroup, State


class AddIdleProxiesStates(StatesGroup):
    to_who = State()
    list = State()