from aiogram.fsm.state import StatesGroup, State


class WalletDataStates(StatesGroup):
    private_key = State()
    confirmation = State()