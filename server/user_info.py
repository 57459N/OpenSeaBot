import json
import os.path
from dataclasses import dataclass, asdict
from enum import Enum

from server import config


class UserStatus(str, Enum):
    inactive = 'Inactive'
    active = 'Active'
    banned = 'Banned'


@dataclass
class UserInfo:
    status: str
    balance: float

    def __init__(self, path: str):
        if not os.path.exists(path):
            raise ValueError(f'UserInfo file not found')

        if os.path.getsize(path) == 0:
            raise ValueError(f'UserInfo is empty')

        self.path = path

    def load(self):
        with open(self.path, 'r') as f:
            _json = json.load(f)

        self.status = _json['status']
        self.balance = _json['balance']

    def save(self):

        with open(self.path, 'w') as f:
            # Convert the status to its string value for saving
            json.dump(self.__dict__, f)

    def increase_balance_and_activate(self, amount: float):
        self.balance += amount
        if self.status == UserStatus.inactive and self.balance >= config.sub_cost:
            self.balance -= config.sub_cost
            self.status = UserStatus.active

    def decrease_balance_or_deactivate(self, amount: float):
        if self.balance < config.sub_cost:
            self.status = UserStatus.inactive
        else:
            self.balance -= amount

    def __enter__(self):
        self.load()
        return self

    def __exit__(self, *exc_details):
        self.save()