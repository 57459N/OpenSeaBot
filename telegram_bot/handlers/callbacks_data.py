from aiogram.filters.callback_data import CallbackData


class PaginationCallback(CallbackData, prefix='pag'):
    page: int
    action: str


class SelectCallback(CallbackData, prefix='sel'):
    page: int
    option: str


class InstrumentCallback(CallbackData, prefix='inst'):
    inst: str = None
    act: str = None
    param: str = None


class UnitCallbackData(CallbackData, prefix='unit'):
    uid: str
    action: bool
