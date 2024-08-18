import pathlib
import sys
import aiohttp
import loguru
from typing import Union, Dict, Any


sys.path.append(str(pathlib.Path(__file__).parent.parent.parent.parent))
import config


class PriceRequests:
    def __init__(self):
        self.session = aiohttp.ClientSession(f'http://{config.SERVER_HOST_IP}:{config.SERVER_HOST_PORT}')

    async def get_items_values(self, *slugs: str) -> Union[Dict[str, Any], float, str, None]:
        async with aiohttp.ClientSession(f'http://{config.SERVER_HOST_IP}:{config.SERVER_HOST_PORT}') as s:
         async with s.post(f'/price_parser/get_prices?token={config.BOT_API_TOKEN}', json=slugs) as r:
            try:
                return await r.json()
            except Exception as e:
                loguru.logger.error(f'Error while requesting items prices from server\n{e}')
                return {}

    async def submit_items(self, *slugs: str) -> None:
        async with aiohttp.ClientSession(f'http://{config.SERVER_HOST_IP}:{config.SERVER_HOST_PORT}') as s:
         await s.post(f'/price_parser/add_collections?token={config.BOT_API_TOKEN}', json=slugs)


price_requests = PriceRequests()
