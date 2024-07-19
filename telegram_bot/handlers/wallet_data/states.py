from aiogram.fsm.state import StatesGroup, State


class WalletDataStates(StatesGroup):
    address = State()
    private_key = State()
    confirmation = State()