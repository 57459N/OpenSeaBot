from aiogram.fsm.state import StatesGroup, State


class GiveDaysStates(StatesGroup):
    main = State()
    usernames = State()
    choosing_usernames = State()
    amount = State()
    confirm = State()
