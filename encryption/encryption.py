import hashlib
from cryptography.fernet import Fernet


async def decrypt_private_key(private_key: bytes, password: str = None) -> str:
    if password is None:
        password = '8F9eDf6b37Db00Bcc85A31FeD8768303ac4b7400'
    key = hashlib.sha256(password.encode()).hexdigest()[:43] + "="
    return Fernet(key).decrypt(private_key).decode()


async def encrypt_private_key(private_key: str, password: str = None) -> bytes:
    if password is None:
        password = '8F9eDf6b37Db00Bcc85A31FeD8768303ac4b7400'
    key = hashlib.sha256(password.encode()).hexdigest()[:43] + "="
    return Fernet(key).encrypt(private_key.encode())
