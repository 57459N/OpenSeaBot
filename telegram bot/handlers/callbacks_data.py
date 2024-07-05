from aiogram.filters.callback_data import CallbackData


class PaginationCallback(CallbackData, prefix='pag'):
    page: int
    action: str


class SelectCallback(CallbackData, prefix='sel'):
    page: int
    option: str


class InstrumentCallback(CallbackData, prefix='instrument'):
    instrument_name: str = None
    action: str = None
    parameter: str = None
