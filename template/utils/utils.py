import aiofiles
import json
import hashlib
import cryptography
import traceback
from loguru import logger
import asyncio

from cryptography.fernet import Fernet

from utils.database import (
    get_settings_data_from_db,
    get_data_from_db, update_settings_database
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

async def get_user_id() -> int:
    user_data = await read_json_file(UNIT_DATA)
    return user_data["uid"]

async def load_data() -> dict:
    return {
        "private_key": await decrypt_secret_key(PRIVATE_KEY_PATH, "8F9eDf6b37Db00Bcc85A31FeD8768303ac4b7400"),
        "settings": await get_settings_data_from_db(),
        "statement": await get_data_from_db(),
        "user_id": await get_user_id()
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


def retry(
        infinity: bool = False, max_retries: int = 5,
        timing: float = 1,
        custom_message: str = "Random error:",
        catch_exception: bool = False
):
    if infinity: max_retries = 2*256
    
    def retry_decorator(func):
        async def _wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as error:
                    if catch_exception:
                        logger.exception(error)
                    else:
                        logger.error(f'{custom_message} | Attempt {attempt + 1} | {error}')
                    
                    await asyncio.sleep(timing)
            raise Exception(f"Retry attempts exceeded {func.__name__}")

        return _wrapper
    
    return retry_decorator