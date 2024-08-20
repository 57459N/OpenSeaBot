import asyncio
import json
import pathlib
import sys
import loguru
from typing import Union, Dict, Any

sys.path.append(str(pathlib.Path(__file__).parent.parent.parent.parent))
import config


class PriceRequests:
    async def get_items_values(self, *slugs: str) -> Union[Dict[str, Any], float, str, None]:
        resp = await self.send_command('get_prices', slugs)
        return resp.get('prices')

    async def submit_items(self, *slugs: str) -> None:
        await self.send_command('add_collections', slugs)

    async def send_command(self, command: str, items: [str]):
        writer = None
        try:
            reader, writer = await asyncio.open_connection(config.PRICE_PARSER_IP, config.PRICE_PARSER_PORT)
            request = {"command": command, "items": items}
            writer.write(json.dumps(request).encode())
            data = await reader.read(2048)
            resp = json.loads(data.decode())

            if resp.get('status') == 'error':
                loguru.logger.error(f'Error from price parser server: {resp.get("message")}')
                raise Exception(resp.get('message'))

            return resp
        except Exception as e:
            loguru.logger.error(f'PriceRequests: {e}')
        finally:
            if writer:
                writer.close()
                await writer.wait_closed()


price_requests = PriceRequests()
