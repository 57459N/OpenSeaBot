import itertools
import os
from telegram_bot import config

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from telegram_bot.handlers.callbacks_data import SelectCallback, PaginationCallback, InstrumentCallback

from telegram_bot.utils.api import INSTRUMENTS


def get_choose_keyboard(options: [str], selected: [str] = None, page: int = 0) -> InlineKeyboardMarkup:
    if selected is None:
        selected = []

    rows = 5
    columns = 2
    items_per_page = rows * columns

    selected = set(selected)

    max_page = (len(options) - 1) // items_per_page + 1
    start_index = page * items_per_page
    end_index = start_index + items_per_page

    builder = InlineKeyboardBuilder()

    buttons = []
    for option in options[start_index:end_index]:
        buttons.append(InlineKeyboardButton(text=f'{"✅" if option in selected else ""}{option}',
                                            callback_data=SelectCallback(page=page, option=option).pack()))

    if page > 0:
        buttons.append(InlineKeyboardButton(
            text="⬅️", callback_data=PaginationCallback(action="paginate", page=page - 1).pack()))
    if page < max_page - 1:
        buttons.append(InlineKeyboardButton(
            text="➡️", callback_data=PaginationCallback(action="paginate", page=page + 1).pack()))

    builder.row(*buttons, width=columns)
    builder.row(InlineKeyboardButton(text="Выбрать", callback_data=PaginationCallback(action="end", page=page).pack()))
    builder.row(InlineKeyboardButton(text="Назад", callback_data="back"))
    return builder.as_markup()


def get_no_sub_keyboard() -> InlineKeyboardMarkup:
    return (InlineKeyboardBuilder()
            .add(InlineKeyboardButton(text="Наш сайт", url=config.LINK_TO_WEBSITE))
            .add(InlineKeyboardButton(text="Подписка", url=config.LINK_TO_SUBSCRIBE))
            # .add(InlineKeyboardButton(text="Мой тг айди", callback_data='get_user_tgid'))
            .adjust(2)
            .as_markup())


def get_support_keyboard() -> InlineKeyboardMarkup:
    return (InlineKeyboardBuilder()
            .add(InlineKeyboardButton(text="Написать в Support", url=config.LINK_TO_SUPPORT))
            .add(InlineKeyboardButton(text="Закрыть", callback_data='delete_message'))
            .as_markup())


def get_welcome_keyboard(is_admin: bool, uid: int):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Информация nо подписке", callback_data='sub_info'))
    builder.add(InlineKeyboardButton(text="Управление подпиской", callback_data='sub_manage'))
    builder.add(InlineKeyboardButton(text="Написать в Support",
                                     url=config.LINK_TO_SUPPORT))

    is_super = uid == 536908900

    if is_admin or is_super:
        builder.add(InlineKeyboardButton(text="Админ меню", callback_data='admin_menu'))
    if is_super:
        builder.add(InlineKeyboardButton(text="Dev", callback_data='dev'))

    builder.adjust(2, 1, 1)

    return builder.as_markup()


def get_sub_info_keyboard():
    return (InlineKeyboardBuilder()
            .add(InlineKeyboardButton(text="Продлить подписку", callback_data='sub_extend'))
            .add(InlineKeyboardButton(text="Обновить информацию", callback_data='sub_info_reload'))
            .add(InlineKeyboardButton(text="Назад", callback_data='back'))
            .adjust(1, 1)
            .as_markup())


def get_sub_extend_generate_keyboard():
    return (InlineKeyboardBuilder()
            .add(InlineKeyboardButton(text="Сгенерировать кошелек", callback_data='sub_extend_generate'))
            .add(InlineKeyboardButton(text="Закрыть", callback_data='delete_message'))
            .adjust(1, 1)
            .as_markup())


def get_sub_extend_to_main_menu_keyboard():
    return (InlineKeyboardBuilder()
            .add(InlineKeyboardButton(text="На главное меню", callback_data='back'))
            .adjust(1)
            .as_markup())


def get_delete_keyboard():
    return (InlineKeyboardBuilder()
            .add(InlineKeyboardButton(text="Закрыть", callback_data='delete_message'))
            .adjust(1)
            .as_markup())


def get_admin_menu_keyboard():
    return (InlineKeyboardBuilder()
            .add(InlineKeyboardButton(text="Выдача дней", callback_data='givedays'))
            .add(InlineKeyboardButton(text="Рассылка", callback_data='broadcast'))
            .add(InlineKeyboardButton(text="Закрыть", callback_data='delete_message'))
            .adjust(1, 1, 1)
            .as_markup())


def get_givedays_type_keyboard():
    return (InlineKeyboardBuilder()
            .add(InlineKeyboardButton(text="Всем", callback_data='givedays_all'))
            .add(InlineKeyboardButton(text="Активным", callback_data='givedays_active'))
            .add(InlineKeyboardButton(text="По Username", callback_data='givedays_usernames'))
            .add(InlineKeyboardButton(text="Назад", callback_data='back'))
            .adjust(1, 1, 1, 1)
            .as_markup())


def get_usernames_keyboard():
    return (InlineKeyboardBuilder()
            .add(InlineKeyboardButton(text="Выбрать username", callback_data='givedays_usernames_choose'))
            .add(InlineKeyboardButton(text="Готово", callback_data='givedays_usernames_enter'))
            .add(InlineKeyboardButton(text="Назад", callback_data='back'))
            .adjust(1, 1)
            .as_markup())


def get_givedays_amount_keyboard():
    return (InlineKeyboardBuilder()
            .add(InlineKeyboardButton(text="7", callback_data='givedays_amount_7'))
            .add(InlineKeyboardButton(text="15", callback_data='givedays_amount_15'))
            .add(InlineKeyboardButton(text="30", callback_data='givedays_amount_30'))
            .add(InlineKeyboardButton(text="Назад", callback_data='back'))
            .adjust(3, 1)
            .as_markup())


def get_confirm_keyboard():
    return (InlineKeyboardBuilder()
            .add(InlineKeyboardButton(text="Да", callback_data='confirm_yes'))
            .add(InlineKeyboardButton(text="Нет", callback_data='confirm_no'))
            .add(InlineKeyboardButton(text="Назад", callback_data='back'))
            .adjust(2, 1)
            .as_markup())


def get_broadcast_keyboard():
    return (InlineKeyboardBuilder()
            .add(InlineKeyboardButton(text="Активным", callback_data='broadcast_active'))
            .add(InlineKeyboardButton(text="Неактивным", callback_data='broadcast_nonactive'))
            .add(InlineKeyboardButton(text="Всем", callback_data='broadcast_all'))
            .add(InlineKeyboardButton(text="Назад", callback_data='back'))
            .adjust(1, 1, 1, 1)
            .as_markup())


def get_broadcast_content_keyboard():
    return (InlineKeyboardBuilder()
            .add(InlineKeyboardButton(text="Готово", callback_data='broadcast_content_ready'))
            .add(InlineKeyboardButton(text="Назад", callback_data='back'))
            .adjust(1, 1)
            .as_markup())


def get_broadcast_confirm_keyboard():
    return (InlineKeyboardBuilder()
            .add(InlineKeyboardButton(text="Да", callback_data='broadcast_confirm_yes'))
            .add(InlineKeyboardButton(text="Нет", callback_data='confirm_no'))
            .adjust(1, 1)
            .as_markup())


def get_dev_keyboard():
    return (InlineKeyboardBuilder()
            .add(InlineKeyboardButton(text="Create", callback_data='dev_create'))
            .add(InlineKeyboardButton(text="Start", callback_data='dev_start'))
            .add(InlineKeyboardButton(text="Stop", callback_data='dev_stop'))
            .add(InlineKeyboardButton(text="Настройки", callback_data=InstrumentCallback(act='settings',
                                                                                         inst="BaseInstrument",
                                                                                         param='None').pack()))

            .add(InlineKeyboardButton(text="Закрыть", callback_data='delete_message'))
            .as_markup())


def get_just_back_button_keyboard():
    return (InlineKeyboardBuilder()
            .add(InlineKeyboardButton(text="Назад", callback_data='back'))
            .as_markup())


def get_instruments_keyboard():
    b = InlineKeyboardBuilder()
    b.add(InlineKeyboardButton(text="Инфо", callback_data=InstrumentCallback(act='info',
                                                                             inst='None',
                                                                             param='None').pack()))

    for i in INSTRUMENTS:
        b.add(InlineKeyboardButton(text=i.name, callback_data=InstrumentCallback(inst=i.name,
                                                                                 act='menu',
                                                                                 param='None').pack()))
    b.add(InlineKeyboardButton(text="Назад", callback_data='back'))

    b.adjust(2)
    return b.as_markup()


def get_instrument_keyboard(instrument_name: str):
    return (InlineKeyboardBuilder()
            .add(InlineKeyboardButton(text="Старт", callback_data=InstrumentCallback(act='start',
                                                                                     inst=instrument_name,
                                                                                     param='None').pack()))
            .add(InlineKeyboardButton(text="Стоп", callback_data=InstrumentCallback(act='stop',
                                                                                    inst=instrument_name,
                                                                                    param='None').pack()))
            .add(InlineKeyboardButton(text="Настройки", callback_data=InstrumentCallback(act='settings',
                                                                                         inst=instrument_name,
                                                                                         param='None').pack()))
            .add(InlineKeyboardButton(text="Назад", callback_data='back'))
            .adjust(2, 2)
            .as_markup())


def get_instrument_settings_keyboard(instrument_name: str, fields: list[str]):
    b = InlineKeyboardBuilder()
    for field in fields:
        b.add(InlineKeyboardButton(text=field, callback_data=InstrumentCallback(act='settings_change',
                                                                                inst=instrument_name,
                                                                                param=field).pack()))
    b.add(InlineKeyboardButton(text="Готово", callback_data=InstrumentCallback(act='settings_finish',
                                                                               inst=instrument_name,
                                                                               param='None').pack()))
    b.add(InlineKeyboardButton(text="Назад", callback_data='back'))
    b.adjust(2)
    return b.as_markup()
