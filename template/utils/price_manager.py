import pathlib
import sys
import aiohttp
import loguru
from typing import Union, Dict, Any
import threading

sys.path.append(str(pathlib.Path(__file__).parent.parent.parent.parent))
import config


class PriceRequests:
    def __init__(self):
        self.lock = threading.Lock()
        self.server_url = f'http://{config.SERVER_HOST_IP}:{config.SERVER_HOST_PORT}/price_parser'

    async def get_items_values(self, *slugs: str) -> Union[Dict[str, Any], float, str, None]:
        with self.lock:
            async with aiohttp.ClientSession(trust_env=True) as s:
                async with s.post(f'{self.server_url}/get_prices?token={config.BOT_API_TOKEN}', json=slugs) as r:
                    try:
                        return await r.json()
                    except Exception as e:
                        loguru.logger.error(f'Error while requesting items prices from server\n{e}')
                        return {}

    async def submit_items(self, *slugs: str) -> None:
        with self.lock:
            async with aiohttp.ClientSession(trust_env=True) as s:
                await s.post(f'{self.server_url}/add_collections?token={config.BOT_API_TOKEN}', json=slugs)


price_requests = PriceRequests()
