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
    create: InitVar[bool] = False

    uid: int = -1
    status: str = UserStatus.inactive.value
    balance: float = 0.0
    bot_wallet: str = ""

    def __post_init__(self, path: str, create: bool = False):
        self.path = path

        if not os.path.exists(path):
            if create:
                self.save()
            else:
                raise ValueError(f'UserInfo file not found')

        if os.path.getsize(path) == 0:
            raise ValueError(f'UserInfo is empty')

    def load(self):
        with open(self.path, 'r') as f:
            _json = json.load(f)
            self.__dict__.update(_json)

    def save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, 'w') as f:
            json.dump(asdict(self), f, indent=2)

    def increase_balance_and_activate(self, amount: float) -> bool:
        ''':returns True if user was activated else False '''
        self.balance += amount
        # user already paid once, and we let hшm activate sub for a day
        # or user didn't pay monthly sub yet
        if (self.status == UserStatus.deactivated and self.balance >= config.SUB_COST_DAY) or \
                (self.status == UserStatus.inactive and self.balance >= config.SUB_COST_MONTH):
            self.balance -= config.SUB_COST_DAY
            self.status = UserStatus.active
            return True

        return False

    def decrease_balance_or_deactivate(self, amount: float) -> bool:
        ''':returns True if sub is successfully paid else False'''
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
