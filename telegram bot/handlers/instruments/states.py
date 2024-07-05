from aiogram.fsm.state import StatesGroup, State


class InstrumentStates(StatesGroup):
    settings_change = State()
