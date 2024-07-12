from utils.paths import *


import hashlib
from cryptography.fernet import Fernet
import json
import cryptography


# todo: make sure in server.misc `_encrypt_private_key` the function is the same
def encode_wallets(password: str, file_data: str) -> bool:
    key = hashlib.sha256(password.encode()).hexdigest()[:43] + "="
    f = Fernet(key)

    encrypted = f.encrypt(file_data.encode())

    with open(PRIVATE_KEY_PATH, 'wb') as file:
        file.write(encrypted)