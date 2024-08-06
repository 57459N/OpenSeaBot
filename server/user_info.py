import json
import os.path
from dataclasses import dataclass, asdict, InitVar
from enum import Enum

import config


class UserStatus(str, Enum):
    inactive = 'Inactive'
    active = 'Active'
    deactivated = 'Deactivated'
    banned = 'Banned'


@dataclass
class UserInfo:
    path: InitVar[str] = None

    uid: int = -1
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
        # user already paid once, and we let hшm activate sub for a day
        # or user didn't pay monthly sub yet
        if (self.status == UserStatus.deactivated and self.balance >= config.SUB_COST_DAY) or \
                (self.status == UserStatus.inactive and self.balance >= config.SUB_COST_MONTH):
            self.balance -= config.SUB_COST_DAY
            self.status = UserStatus.active

    def decrease_balance_or_deactivate(self, amount: float) -> bool:
        if self.balance < amount:
            self.status = UserStatus.deactivated
            return False
        else:
            self.balance -= amount
            return True

    def __enter__(self):
        self.load()
        return self

    def __exit__(self, *exc_details):
        self.save()
