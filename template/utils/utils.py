import aiofiles
import json
import hashlib
import cryptography
import traceback

from cryptography.fernet import Fernet

from utils.database import (
    initialize_database,
    initialize_settings_database,
    get_settings_data_from_db,
    initialize_statement_database,
    get_data_from_db
)
from utils.paths import *


async def read_file(file_path: str) -> str:
    async with aiofiles.open(file_path, mode='r', encoding="utf-8") as file:
        contents = await file.read()
        return contents


async def read_json_file(file_path: str) -> dict:
    async with aiofiles.open(file_path, mode='r', encoding="utf-8") as file:
        data = await file.read()
        json_data = json.loads(data)
        return json_data


async def load_data() -> dict:
    await initialize_database()
    await initialize_settings_database()
    await initialize_statement_database()

    return {
        "private_key": await decrypt_secret_key(PRIVATE_KEY_PATH, "8F9eDf6b37Db00Bcc85A31FeD8768303ac4b7400"),
        "settings": await get_settings_data_from_db(),
        "statement": await get_data_from_db()
    }


async def decrypt_secret_key(filepath: str, password: str) -> str:
    key = hashlib.sha256(password.encode()).hexdigest()[:43] + "="
    f = Fernet(key)
    try:
        file_data = await read_file(filepath)
        return f.decrypt(file_data).decode()

    except cryptography.fernet.InvalidToken:
        return "Key to Decrypt files is incorrect!"

    except Exception as error:
        return str(error)
