from aiogram.fsm.state import StatesGroup, State

class CreateUnitStates(StatesGroup):
    uid = State()