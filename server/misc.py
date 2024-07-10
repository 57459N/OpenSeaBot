import json
import logging
import os
import shutil
import sys

from dataclasses import dataclass
from socket import socket, AF_INET, SOCK_STREAM
from subprocess import Popen
from typing import Any

from server import config

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


def update_userinfo(uid: int | str, data: dict[str, Any]):
    info = get_userinfo(uid)
    info.update(data)

    path = f'./units/{uid}/.userinfo'
    dirs = path[:path.rfind('/')]
    os.makedirs(dirs, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(info, f)


def get_userinfo(uid: int | str) -> dict[str, Any]:
    path = f'./units/{uid}/.userinfo'
    dirs = path[:path.rfind('/')]
    os.makedirs(dirs, exist_ok=True)
    if os.path.exists(path) and os.path.getsize(path) > 0:
        with open(path, 'r') as f:
            return json.load(f)
    return {}


def validate_token(token: str) -> bool:
    return token == config.token

def unit_exists(uid: int) -> bool:
    return os.path.exists(f'./units/{uid}/unit.py')