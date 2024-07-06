from dataclasses import dataclass
from socket import socket, AF_INET, SOCK_STREAM
from subprocess import Popen

import logging
import sys

logging.basicConfig(level=logging.INFO, stream=sys.stdout)


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
    process = Popen([sys.executable, f'unit.py', f'{port}'], cwd=f'./units/{uid}')
    unit = Unit(port=port, process=process)
    logging.info(f'SERVER:INIT_UNIT: unit {uid} initialized on port {port}')
    return unit
