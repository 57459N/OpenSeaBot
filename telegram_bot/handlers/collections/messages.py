import os
import re

import aiofiles
from aiogram import Router, types, flags
from aiogram.fsm.context import FSMContext
from aiogram.types import File

from handlers.collections.states import CollectionsStates

router = Router()


@router.message(CollectionsStates.set_list)
async def set_collections_message_handler(message: types.Message, state: FSMContext):
    text = message.text

    if text is None:
        doc = message.document
        file: File = await message.bot.get_file(doc.file_id)
        if not os.path.exists('./tmp/'):
            os.makedirs('./tmp/')

        new_filepath = f'./tmp/{file.file_id}'
        await message.bot.download_file(file.file_path, new_filepath)
        async with aiofiles.open(new_filepath, 'r', encoding='utf-8') as f:
            text = await f.read()
        os.remove(new_filepath)

    added_proxies = re.split(r'[\n ]+', text)
    data = await state.get_data()
    proxies_list = data.get('collections', None)
    if proxies_list is None:
        proxies_list = []
    proxies_list.extend(added_proxies)
    await message.delete()
    await state.update_data(collections=proxies_list)
