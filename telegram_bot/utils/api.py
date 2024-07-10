import asyncio
import logging
import random
from typing import Any
from datetime import datetime
import aiohttp
from aiogram import Bot, types

from telegram_bot.utils.instrument import Instrument, Instruments
from telegram_bot.config import SERVER_HOST_IP, SERVER_HOST_PORT



# todo: call the API
async def get_user_subscription_info_by_id(uid: int) -> {'str': Any}:
    logging.info(f'SUB_INFO: requesting subscription info for user uid={uid}')
    async with aiohttp.ClientSession() as session:
        async with session.get(f'http://{SERVER_HOST_IP}:{SERVER_HOST_PORT}/user/get_info?uid={uid}') as resp:
            if resp.status == 200 and 'json' in resp.content_type:
                return await resp.json()



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
    async with aiohttp.ClientSession() as session:
        async with session.get(
                f'http://{SERVER_HOST_IP}:{SERVER_HOST_PORT}/server/get_wallet_to_extend_sub?uid={uid}') as resp:
            if resp.status == 200 and 'json' in resp.content_type:
                return await resp.json()
            else:
                logging.error(f'WALLET: error requesting wallet address for user uid={uid}\n{resp}')
                return None


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


async def get_usernames(bot: Bot, status: str = None) -> list[str] | None:
    users = await get_users(bot, status)
    usernames = [u.username if u.username else '`Empty`' for u in users]
    return usernames


async def get_users(bot: Bot, status: str = None) -> tuple[types.ChatFullInfo] | None:
    user_ids = await get_user_ids(status)
    return await asyncio.gather(*(bot.get_chat(uid) for uid in user_ids))


async def get_user_ids(status: str = None) -> list[int] | None:
    logging.info('USER_IDS: requesting user_ids from server')
    async with aiohttp.ClientSession() as session:
        url = f'http://{SERVER_HOST_IP}:{SERVER_HOST_PORT}/server/get_user_ids'
        async with session.get(url) as resp:
            try:
                if 'json' in resp.content_type:
                    return (await resp.json())['user_ids']
                else:
                    raise ValueError('Bad response')
            except ValueError:
                logging.error('USER_IDS: bad response type, expected json')
            except KeyError:
                logging.error('USER_IDS: bad response, expected `user_ids` key')
            return None


INSTRUMENTS = Instruments(
    Instrument(name='BaseInstrument',
               server_name='unit'),
)


async def send_server_command(command: str, data: dict[str, Any]) -> bool | dict:
    async with aiohttp.ClientSession() as session:
        url = f'http://{SERVER_HOST_IP}:{SERVER_HOST_PORT}/unit/{command}?{"&".join(f"{k}={v}" for k, v in data.items())}'
        async with session.get(url) as resp:
            if 'json' in resp.content_type:
                return await resp.json()
            elif 200 <= resp.status < 300:
                return True
            return False


async def increase_user_balance(uid, paid_amount, token):
    async with aiohttp.ClientSession() as session:
        url = f'http://{SERVER_HOST_IP}:{SERVER_HOST_PORT}/user/increase_balance?uid={uid}&amount={paid_amount}&token={token}'
        async with session.get(url) as resp:
            return 200 <= resp.status < 300

