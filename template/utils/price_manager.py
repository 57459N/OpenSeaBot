import aiohttp
import loguru
from typing import Union, Dict, Any
import config


class PriceRequests:
    def __init__(self):
        self.session = aiohttp.ClientSession(f'http://{config.SERVER_HOST_IP}:{config.SERVER_HOST_PORT}')

    async def get_items_values(self, *slugs: str) -> Union[Dict[str, Any], float, str, None]:
        async with self.session.post(f'price_parser/get_prices', json=slugs) as r:
            try:
                return await r.json()
            except Exception as e:
                loguru.logger.error(f'Error while requesting items prices from server\n{e}')
                return {}

    async def submit_items(self, *slugs: str) -> None:
        await self.session.post(f'price_parser/add_collections', json=slugs)


price_requests = PriceRequests()
