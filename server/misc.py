import asyncio
import hashlib
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
from cryptography.fernet import Fernet

import config
import payments
from server.user_info import UserInfo, UserStatus


async def _get_proxies(filepath: str, amount: int) -> list[str]:
    with open('.idle_proxies', 'r') as _in:
        lines = _in.readlines()
        if len(lines) < amount:
            raise IndexError(f'Not enough free proxies. Need {amount}, but got only {len(lines)} in {filepath}')

    with open('.idle_proxies', 'w') as _out:
        _out.writelines(lines[amount:])

    return list(map(lambda x: x.strip(), lines[:amount]))


async def _encrypt_private_key(private_key: str, password: str) -> bytes:
    key = hashlib.sha256(password.encode()).hexdigest()[:43] + "="
    return Fernet(key).encrypt(private_key.encode())


async def create_unit(uid: int):
    try:
        shutil.copytree('./template', f'./units/{uid}', dirs_exist_ok=True)
    except Exception:
        loguru.logger.error(f'SERVER:CREATE_UNIT: Error with COPY TEMPLATE while creating unit for user {uid}')
        raise Exception(f'Не удалось создать юнит пользователя {uid}. Ошибка при копировании шаблона')

    try:
        with open(f'./units/{uid}/data/private_key.txt', 'wb') as pk_o, UserInfo(f'./units/{uid}/.userinfo') as ui:
            account = await payments.generate_account()

            ui.const_bot_wallet = account['address']

            private_key = account['secret']
            encrypted = await _encrypt_private_key(private_key, '8F9eDf6b37Db00Bcc85A31FeD8768303ac4b7400')
            pk_o.write(encrypted)
    except Exception:
        loguru.logger.error(f'SERVER:CREATE_UNIT: Error with CONFIG FILES while creating unit for user {uid}')
        raise Exception(f'Не удалось создать юнит пользователя {uid}. Ошибка при создании аккаунта бота')

    try:
        with open(f'./units/{uid}/proxies.txt', 'w') as f:
            proxies = await _get_proxies('.idle_proxies', config.PROXIES_PER_USER)
            f.write('\n'.join(proxies))
    except IndexError as e:
        raise Exception(f'Не удалось создать юнит пользователя {uid}. Недостаточно свободных прокси\n{e}')


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
        loguru.logger.warning(f'SERVER:INIT_UNIT: unit {uid} is not found')
        return None

    process = Popen([sys.executable, f'unit.py', f'{port}'], cwd=f'./units/{uid}')
    unit = Unit(port=port, process=process)
    loguru.logger.info(f'SERVER:INIT_UNIT: unit {uid} initialized on port {port}')
    return unit


def validate_token(token: str) -> bool:
    return token == config.BOT_API_TOKEN


def unit_exists(uid: int) -> bool:
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
                        async with aiohttp.ClientSession() as session:
                            async with session.get(
                                    url=f"http://127.0.0.1:{app['active_units'][uid].port}/is_running") as resp:
                                is_running = await resp.text() == 'True'
                                if is_running:
                                    await session.get(url=f"http://127.0.0.1:{app['active_units'][uid].port}/stop")
                        continue

                    if ui.decrease_balance_or_deactivate(config.SUB_COST):
                        loguru.logger.info(f"SERVER:DAILY_SUB_BALANCE_DECREASE: {uid} sub is paid")
                    else:
                        loguru.logger.info(f"SERVER:DAILY_SUB_BALANCE_DECREASE: {uid} sub is not paid")

            except ValueError as e:
                loguru.logger.warning(
                    f"SERVER:DAILY_SUB_BALANCE_DECREASE: {uid} directory doesn't contain .userinfo file\n{e}")


async def send_message_to_support(message: str):
    text = f'`❗OpenSea Bot Error Message❗\n\n{message}`'
    async with aiohttp.ClientSession() as session:
        resp = await session.post(url=f'https://api.telegram.org/bot{config.BOT_API_TOKEN}/sendMessage',
                                  data={'chat_id': config.SUPPORT_UID, 'text': text})


# from web3 import Web3, AsyncHTTPProvider
# from web3.eth import AsyncEth

async def get_wallet_balance(const_bot_wallet: str) -> float | str:
    # w3 = Web3(
    #         Web3.AsyncHTTPProvider(
    #             "https://1rpc.io/eth",
    #             request_kwargs={"ssl": False}
    #         ),
    #         modules={"eth": (AsyncEth,)},
    #         middlewares=[]
    #     )
    # balance = await w3.eth.get_balance(const_bot_wallet)
    # return w3.from_wei(balance, 'ether')

    return "TEST BOT BALANCE. TODO: IMPLEMENT"


async def add_proxies(filepath: str, proxies: list[str]):
    def process(proxy: str):
        return proxy.strip() + '\n'

    async with aiofiles.open(filepath, 'a') as f:
        await f.writelines(list(map(process, proxies)))
