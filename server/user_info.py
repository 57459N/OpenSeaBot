import json
import os.path
from dataclasses import dataclass, asdict
from enum import Enum


class UserStatus(str, Enum):
    inactive = 'Inactive'
    active = 'Active'
    banned = 'Banned'


@dataclass
class UserInfo:
    status: str
    balance: float

    def __init__(self, uid: int | str):
        self.uid = uid

    def load(self):
        path = f'./units/{self.uid}/.userinfo'
        if not os.path.exists(path):
            raise ValueError(f'User {self.uid} not found')

        if os.path.getsize(path) == 0:
            raise ValueError(f'User info {self.uid} is empty')

        with open(path, 'r') as f:
            _json = json.load(f)

        self.status = _json['status']
        self.balance = _json['balance']

    def save(self):
        path = f'./units/{self.uid}/.userinfo'
        with open(path, 'w') as f:
            # Convert the status to its string value for saving
            json.dump(self.__dict__, f)

    def __enter__(self):
        self.load()
        return self

    def __exit__(self, *exc_details):
        self.save()
