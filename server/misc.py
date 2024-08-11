import asyncio
import hashlib
import subprocess

import loguru
import os
import shutil
import sys

from dataclasses import dataclass
from datetime import datetime, timedelta
from socket import socket, AF_INET, SOCK_STREAM
from subprocess import Popen

import aiofiles
import aiohttp
from aiohttp import web

import config
from encryption.system import encrypt_private_key
from payments.system import manager as payments_manager
from server.user_info import UserInfo, UserStatus


async def _get_proxies(filepath: str, amount: int) -> list[str]:
    with open('.idle_proxies', 'r') as _in:
        lines = _in.readlines()
        if len(lines) < amount:
            raise IndexError(f'Not enough free proxies. Need {amount}, but got only {len(lines)} in {filepath}')

    with open('.idle_proxies', 'w') as _out:
        _out.writelines(lines[amount:])

    return list(map(lambda x: x.strip(), lines[:amount]))


async def create_unit(uid: int | str):
    if os.path.exists(f'./units/{uid}'):
        loguru.logger.error(f'SERVER:CREATE_UNIT: Unit {uid} already exists')
        raise Exception(f'Юнит {uid} уже существует')

    try:
        shutil.copytree('./template', f'./units/{uid}', dirs_exist_ok=True)
    except Exception:
        loguru.logger.error(f'SERVER:CREATE_UNIT: Error with COPY TEMPLATE while creating unit for user {uid}')
        raise Exception(f'Не удалось создать юнит пользователя {uid}. Ошибка при копировании шаблона')

    try:
        with open(f'./units/{uid}/data/private_key.txt', 'wb') as pk_o, UserInfo(f'./units/{uid}/.userinfo') as ui:
            ui.uid = int(uid)

            account = await payments_manager.generate_account()
            ui.bot_wallet = account['address']
            private_key = account['secret']
            # make sure password here match with password in template
            encrypted = await encrypt_private_key(private_key)
            pk_o.write(encrypted)
    except Exception:
        loguru.logger.error(f'SERVER:CREATE_UNIT: Error with CONFIG FILES while creating unit for user {uid}')
        raise Exception(f'Не удалось создать юнит пользователя {uid}. Ошибка при создании аккаунта бота')

    try:
        with open(f'./units/{uid}/proxies.txt', 'w') as f:
            proxies = await _get_proxies('.idle_proxies', config.PROXIES_PER_USER)
            f.write('\n'.join(proxies))
    except IndexError as e:
        loguru.logger.error(f'SERVER:CREATE_UNIT: Error with PROXIES while creating unit for user {uid}')
        raise e


def get_free_port() -> int:
    with socket(AF_INET, SOCK_STREAM) as s:
        s.bind(('localhost', 0))
        return s.getsockname()[1]


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
        loguru.logger.warning(f'SERVER:INIT_UNIT: unit {uid} is not found')
        raise Exception(f'Юнит {uid} не существует')

    process = Popen([sys.executable, f'unit.py', f'{port}'], cwd=f'./units/{uid}')
    unit = Unit(port=port, process=process)
    loguru.logger.info(f'SERVER:INIT_UNIT: unit {uid} initialized on port {port}')
    return unit


def deinit_unit(unit: Unit):
    if unit is None:
        raise ValueError('Unit is None')
    unit.process.terminate()


def validate_token(token: str) -> bool:
    return token == config.BOT_API_TOKEN


def unit_exists(uid: int | str) -> bool:
    return os.path.exists(f'./units/{uid}/unit.py')


async def daily_sub_balance_decrease(app: web.Application):
    while True:
        # todo: maybe rewrite tax collection period to use config's parameter
        now = datetime.now()
        midnight = datetime.combine(now.date() + timedelta(days=1), datetime.min.time())
        seconds_until_midnight = (midnight - now).total_seconds()

        loguru.logger.info(
            f"SERVER:DAILY_SUB_BALANCE_DECREASE: sleeping {seconds_until_midnight} seconds till next tax collection")
        await asyncio.sleep(seconds_until_midnight)

        for uid in os.listdir('./units'):
            if not os.path.isdir(f'./units/{uid}'):
                continue

            try:
                with UserInfo(f'./units/{uid}/.userinfo') as ui:
                    if ui.status != UserStatus.active and uid in app['active_units']:
                        async with aiohttp.ClientSession(trust_env=True) as session:
                            async with session.get(
                                    url=f"http://127.0.0.1:{app['active_units'][uid].port}/is_running") as resp:
                                is_running = await resp.text() == 'True'
                                if is_running:
                                    await session.get(url=f"http://127.0.0.1:{app['active_units'][uid].port}/stop")
                        continue

                    if ui.decrease_balance_or_deactivate(config.SUB_COST_DAY):
                        loguru.logger.info(f"SERVER:DAILY_SUB_BALANCE_DECREASE: {uid} sub is paid")
                    else:
                        loguru.logger.info(f"SERVER:DAILY_SUB_BALANCE_DECREASE: {uid} sub is not paid")

            except ValueError as e:
                loguru.logger.warning(
                    f"SERVER:DAILY_SUB_BALANCE_DECREASE: {uid} directory doesn't contain .userinfo file\n{e}")


async def send_message_to_support(message: str):
    text = f'❗OpenSea Bot Error Message❗\n\n{message}'
    async with aiohttp.ClientSession(trust_env=True) as session:
        resp = await session.post(url=f'http://api.telegram.org/bot{config.BOT_API_TOKEN}/sendMessage',
                                  data={'chat_id': config.SUPPORT_UID, 'text': text, 'parse_mode': 'HTML'}, ssl=False)


async def add_proxies(filepath: str, proxies: list[str], overwrite: bool = False):
    def process(proxy: str):
        return proxy.strip() + '\n'

    mode = 'w' if overwrite else 'a'
    async with aiofiles.open(filepath, mode) as f:
        await f.writelines(list(map(process, proxies)))


def delete_unit(uid: int | str, active_units: dict[str, Unit]):
    if unit := active_units.get(uid):
        unit.process.terminate()
    try:
        shutil.rmtree(f'./units/{uid}')
    except FileNotFoundError:
        raise Exception(f'Unit {uid} not found')
