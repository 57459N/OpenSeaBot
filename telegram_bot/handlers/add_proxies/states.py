from aiogram.fsm.state import StatesGroup, State


class AddProxiesStates(StatesGroup):
    to_who = State()
    user = State()
    list = State()