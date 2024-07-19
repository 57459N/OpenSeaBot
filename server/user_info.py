import json
import os.path
from dataclasses import dataclass, asdict, InitVar
from enum import Enum

import config


class UserStatus(str, Enum):
    inactive = 'Inactive'
    active = 'Active'
    banned = 'Banned'


@dataclass
class UserInfo:
    path: InitVar[str] = None

    status: str = UserStatus.inactive.value
    balance: float = 0.0
    bot_wallet: str = ""

    def __post_init__(self, path: str):
        if not os.path.exists(path):
            raise ValueError(f'UserInfo file not found')

        if os.path.getsize(path) == 0:
            raise ValueError(f'UserInfo is empty')

        self.path = path

    def load(self):
        with open(self.path, 'r') as f:
            _json = json.load(f)
            self.__dict__.update(_json)

    def save(self):
        with open(self.path, 'w') as f:
            json.dump(asdict(self), f, indent=2)

    def increase_balance_and_activate(self, amount: float):
        self.balance += amount
        if self.status == UserStatus.inactive and self.balance >= config.SUB_COST:
            self.balance -= config.SUB_COST
            self.status = UserStatus.active

    def decrease_balance_or_deactivate(self, amount: float) -> bool:
        if self.balance < config.SUB_COST:
            self.status = UserStatus.inactive
            return False
        else:
            self.balance -= amount
            return True

    def __enter__(self):
        self.load()
        return self

    def __exit__(self, *exc_details):
        self.save()
