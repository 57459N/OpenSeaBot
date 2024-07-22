import asyncio
import os.path
import re

import aiofiles
from aiogram import Router, types, flags
from aiogram.fsm.context import FSMContext
from aiogram.types import Document, File

from .states import AddProxiesStates

router = Router()


@router.message(AddProxiesStates.list)
async def add_proxies_message_handler(message: types.Message, state: FSMContext):
    text = message.text

    if text is None:
        doc = message.document
        file: File = await message.bot.get_file(doc.file_id)
        if not os.path.exists('./tmp/'):
            os.makedirs('./tmp/')
        await message.bot.download_file(file.file_path, './tmp/downloaded.txt')
        async with aiofiles.open('./tmp/downloaded.txt', 'r', encoding='utf-8') as f:
            text = await f.read()
        os.remove('./tmp/downloaded.txt')

    added_proxies = re.split(r'[\n ]+', text)
    data = await state.get_data()
    proxies_list = data.get('proxies', None)
    if proxies_list is None:
        proxies_list = []
    proxies_list.extend(added_proxies)
    await message.delete()
    await state.update_data(proxies=proxies_list)


