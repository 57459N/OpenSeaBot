import logging
import random
from typing import Any
from datetime import datetime
import aiohttp

from telegram_bot.utils.instrument import Instrument, Instruments
from telegram_bot.config import SERVER_HOST_IP, SERVER_HOST_PORT


# Function to get user subscription info
# Expects
#   'status': str
#   'end_date': datetime
#   'days_left': int
#   'balance': int
# todo: call the API
async def get_user_subscription_info_by_id(uid: int) -> {'str': Any}:
    logging.info(f'SUB_INFO: requesting subscription info for user uid={uid}')
    end_date = datetime.strptime('2222-01-01', '%Y-%m-%d')
    return {
        'status': 'Active',
        'end_date': end_date,
        'days_left': (end_date - datetime.now()).days,
        'balance': random.randint(100, 1000)
    }


# Checks if user is subscribed
# todo: call the API
async def is_user_subscribed(uid: int) -> bool:
    return True


# Checks if user subscription is active
# todo: remove return True IN PRODUCTION
async def is_users_sub_active(uid: int) -> bool:
    return (await get_user_subscription_info_by_id(uid))['status'] == 'Active'


# Returns wallet address to extend user's subscription
# todo: call the API
async def get_wallet_to_extend_sub(uid):
    logging.info(f'WALLET: requesting wallet address for user uid={uid}')
    return 'aaaaaaaaaaaaaaa Test wallet address bbbbbbbbbbbbb'


# Gives specified type of users or users in usernames amount of days
# Roughly post-request format:
#   {
#       'to_who': 'all' | 'active' | 'usernames'
#       'amount': int
#       'usernames': list of usernames or empty if type is not 'usernames'
#   }
# todo: call the API
async def give_days(*usernames: str, to_who: str, amount: int):
    logging.info(f'SUBS: requesting subs for {amount} days to {to_who} : {usernames}')


# Return all usernames
# todo: call the API
async def get_usernames(status: str = None) -> [str]:
    logging.info('USERNAMES: requesting usernames from server')
    return [f'user_{i}' for i in range(13)]


# todo: Maybe rewrite in two functions - get and set with variable parameter `instrument_name`
# todo: call the API
async def get_instrument_settings(uid: int, instrument: Instrument):
    match instrument.name:
        case 'Floor Lister':
            data = {'a': '1', 'b': '2', 'c': '3'}
        case 'Collection Scanner':
            data = {'d': '4', 'e': '5', 'f': '6'}
        case 'Collection Bidder':
            data = {'g': '7', 'h': '8', 'i': '9'}
        case 'BaseInstrument':
            data = {''}
        case _:
            data = None

    logging.info(f'SETTINGS: requesting {instrument.server_name} settings for user uid={uid}')
    return data


# todo: call the API
async def set_instrument_settings(uid: int, instrument: Instrument, settings: dict):
    logging.info(f'SETTINGS: setting {instrument.server_name}: {settings} settings for user uid={uid}')
    return True


async def start_instrument(uid: int, instrument: Instrument):
    logging.info(f'START: starting {instrument.server_name} for user uid={uid}')
    return await send_server_command(uid, instrument, 'start')


async def stop_instrument(uid: int, instrument: Instrument):
    logging.info(f'STOP: stopping {instrument.server_name} for user uid={uid}')
    return await send_server_command(uid, instrument, 'stop')


INSTRUMENTS = Instruments(
    Instrument(name='Floor Lister',
               server_name='floor_lister'),
    Instrument(name='Collection Scanner',
               server_name='collection_scanner'),
    Instrument(name='Collection Bidder',
               server_name='collection_bidder'),
    Instrument(name='BaseInstrument',
               server_name='unit'),
)


async def send_server_command(uid: int, instrument: Instrument, command: str) -> bool:
    async with aiohttp.ClientSession() as session:
        url = f'http://{SERVER_HOST_IP}:{SERVER_HOST_PORT}/{instrument.server_name}/{command}?uid={uid}'
        async with session.get(url) as resp:
            if 200 <= resp.status < 300:
                return True
            return False
