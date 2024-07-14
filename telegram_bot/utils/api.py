import asyncio
import sys

import loguru
from typing import Any
import aiohttp
from aiogram import Bot, types
from aiohttp import ClientResponse
from aiohttp.web_response import Response

from telegram_bot.utils.instrument import Instrument, Instruments
from config import SERVER_HOST_IP, SERVER_HOST_PORT



async def get_user_subscription_info_by_id(uid: int) -> {'str': Any}:
    loguru.logger.info(f'SUB_INFO: requesting subscription info for user uid={uid}')
    async with aiohttp.ClientSession() as session:
        async with session.get(f'http://{SERVER_HOST_IP}:{SERVER_HOST_PORT}/user/{uid}/get_info') as resp:
            if resp.status == 200 and 'json' in resp.content_type:
                return await resp.json()
            elif resp.status == 404:
                return {}


async def is_user_subscribed(uid: int) -> bool:
    return (await get_user_subscription_info_by_id(uid)) != {}


async def is_users_sub_active(uid: int) -> bool:
    return (await get_user_subscription_info_by_id(uid))['status'] == 'Active'


# Gives specified type of users or users in usernames amount of days
# Roughly post-request format:
#   {
#       'to_who': 'all' | 'active' | 'usernames'
#       'amount': int
#       'usernames': list of usernames or empty if type is not 'usernames'
#   }
# todo: call the API
async def give_days(*uids: str, amount: int):
    loguru.logger.info(f'SUBS: requesting subs for {amount} days to {uids}')


async def get_usernames(bot: Bot, status: str = None) -> list[str] | None:
    users = await get_users(bot, status)
    usernames = [u.username if u.username else '`Empty`' for u in users]
    return usernames


async def get_users(bot: Bot, status: str = None) -> tuple[types.ChatFullInfo] | None:
    user_ids = await get_user_ids(status)
    return await asyncio.gather(*(bot.get_chat(uid) for uid in user_ids))


async def get_user_ids(status: str = None) -> list[int] | None:
    loguru.logger.info('USER_IDS: requesting user_ids from server')
    async with aiohttp.ClientSession() as session:
        url = f'http://{SERVER_HOST_IP}:{SERVER_HOST_PORT}/server/get_user_ids'
        async with session.get(url) as resp:
            try:
                if 'json' in resp.content_type:
                    return (await resp.json())['user_ids']
                else:
                    raise ValueError('Bad response')
            except ValueError:
                loguru.logger.error('USER_IDS: bad response type, expected json')
            except KeyError:
                loguru.logger.error('USER_IDS: bad response, expected `user_ids` key')
            return None


INSTRUMENTS = Instruments(
    Instrument(name='BaseInstrument',
               server_name='unit'),
)


async def send_unit_command(uid: int | str, command: str, data=None) -> int | ClientResponse:
    if data is None:
        data = {}
    async with aiohttp.ClientSession() as session:
        url = f'http://{SERVER_HOST_IP}:{SERVER_HOST_PORT}/unit/{uid}/{command}?{"&".join(f"{k}={v}" for k, v in data.items())}'
        async with session.get(url) as resp:
            if 'json' in resp.content_type:
                return await resp.json()
            else:
                return resp


async def increase_user_balance(uid, paid_amount, token):
    async with aiohttp.ClientSession() as session:
        url = f'http://{SERVER_HOST_IP}:{SERVER_HOST_PORT}/user/{uid}/increase_balance?amount={paid_amount}&token={token}'
        async with session.get(url) as resp:
            return 200 <= resp.status < 300


async def add_proxies(proxies: list[str]) -> bool:
    async with aiohttp.ClientSession() as session:
        url = f'http://{SERVER_HOST_IP}:{SERVER_HOST_PORT}/server/add_proxies'
        async with session.post(url, json=proxies) as resp:
            return 200 <= resp.status < 300
