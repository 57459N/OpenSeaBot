import asyncio
import logging
import os
import shutil
import sys

from dataclasses import dataclass
from datetime import datetime, timedelta
from socket import socket, AF_INET, SOCK_STREAM
from subprocess import Popen

import aiohttp
from aiohttp import web

from server import config
from server.user_info import UserInfo, UserStatus

logging.basicConfig(level=logging.INFO, stream=sys.stdout)


async def _get_proxies(uid: int) -> list[str]:
    return ['proxy1', 'proxy2', 'proxy3']


async def _get_private_key(uid: int) -> str:
    return "TODO: KEY"


async def _encrypt_private_key(private_key: str, password: str) -> str:
    return f"TODO: ENCRYPT KEY: {private_key}"


async def create_unit(uid: int):
    try:
        shutil.copytree('./template', f'./units/{uid}', dirs_exist_ok=True)
    except Exception as e:
        text = f'Error with COPY TEMPLATE while creating unit for user {uid}'
        logging.error(f'SERVER:CREATE_UNIT: {text}')
        raise Exception(text) from e

    try:
        with open(f'./units/{uid}/proxies.txt', 'w') as f:
            proxies = await _get_proxies(uid)
            f.write('\n'.join(proxies))

        with open(f'./units/{uid}/data/private_key.txt', 'w') as f:
            key = await _get_private_key(uid)
            encrypted = await _encrypt_private_key(key, '8F9eDf6b37Db00Bcc85A31FeD8768303ac4b7400')
            f.write(encrypted)
    except Exception as e:
        text = f'Error with CONFIG FILES while creating unit for user {uid}'
        logging.error(f'SERVER:CREATE_UNIT: {text}')
        raise Exception(text) from e


def get_free_port() -> int | None:
    for port in range(1024, 65536):
        try:
            s = socket(AF_INET, SOCK_STREAM)
            s.bind(('localhost', port))
            s.close()
            return port
        except OSError:
            pass


@dataclass
class Unit:
    port: int
    process: Popen

    def __hash__(self):
        return self.port

    def __del__(self):
        try:
            self.process.terminate()
        except Exception:
            pass


def init_unit(uid: str) -> Unit:
    port = get_free_port()
    if not os.path.exists(f'./units/{uid}/unit.py'):
        logging.warning(f'SERVER:INIT_UNIT: unit {uid} is not found')
        return None

    process = Popen([sys.executable, f'unit.py', f'{port}'], cwd=f'./units/{uid}')
    unit = Unit(port=port, process=process)
    logging.info(f'SERVER:INIT_UNIT: unit {uid} initialized on port {port}')
    return unit


def validate_token(token: str) -> bool:
    return token == config.token


def unit_exists(uid: int) -> bool:
    return os.path.exists(f'./units/{uid}/unit.py')


async def daily_sub_balance_decrease(app: web.Application):
    while True:
        now = datetime.now()
        midnight = datetime.combine(now.date() + timedelta(days=1), datetime.min.time())
        seconds_until_midnight = (midnight - now).total_seconds()
        logging.info(
            f"SERVER:DAILY_SUB_BALANCE_DECREASE: sleeping {seconds_until_midnight} seconds till next tax collection")
        await asyncio.sleep(seconds_until_midnight)

        for uid in os.listdir('./units'):
            if not os.path.isdir(f'./units/{uid}'):
                continue

            try:
                with UserInfo(f'./units/{uid}/.userinfo') as ui:
                    if ui.status != UserStatus.active and uid in app['active_units']:
                        async with aiohttp.ClientSession() as session:
                            async with session.get(
                                    url=f"http://127.0.0.1:{app['active_units'][uid].port}/is_running") as resp:
                                is_running = await resp.text() == 'True'
                                if is_running:
                                    await session.get(url=f"http://127.0.0.1:{app['active_units'][uid].port}/stop")
                        continue

                    if ui.decrease_balance_or_deactivate(config.sub_cost):
                        logging.info(f"SERVER:DAILY_SUB_BALANCE_DECREASE: {uid} sub is paid")
                    else:
                        logging.info(f"SERVER:DAILY_SUB_BALANCE_DECREASE: {uid} sub is not paid")

            except ValueError as e:
                logging.warning(
                    f"SERVER:DAILY_SUB_BALANCE_DECREASE: {uid} directory doesn't contain .userinfo file\n{e}")
