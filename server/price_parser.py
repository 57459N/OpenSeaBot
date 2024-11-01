import asyncio
import json

from server.opensea.client import OpenseaAccount
from loguru import logger
from eth_account import Account
from typing import Union, Dict, Any


class ClientsManager:
    def __init__(self, clients: list):
        self.clients = clients
        self.index = 0

    def get(self) -> OpenseaAccount:
        client = self.clients[self.index]
        self.index = (self.index + 1) % len(self.clients)
        return client

    def add_client(self, client):
        self.clients.append(client)

    async def close_sessions(self) -> None:
        for s in self.clients:
            s: OpenseaAccount
            await s.close_session()

    async def sessions_handler(self) -> None:
        logger.info(f'Sessions handler was run!')
        while True:
            try:
                await asyncio.sleep(600)
                tasks = [client.safe_executor(client.login) for client in self.clients]
                await asyncio.gather(*tasks)

            except Exception as error:
                logger.error(error)


class OpenseaParser(ClientsManager):
    def __init__(self, opensea_clients: list):
        super().__init__(opensea_clients)
        self.slug_to_minbid = {}
        self.tasks = {}
        self.stop_signals = {}
        self.opensea_accounts = {}

    async def parse_item(self, item_id: str):
        while not self.stop_signals.get(item_id, False):
            client = self.get()
            price = await self.fetch_price(item_id, client)
            if price:
                self.set_item_value(item_id, price)
                #logger.info(f'NEW price for: {item_id} : {price}')
            await asyncio.sleep(0.2)

    async def fetch_price(self, item_id: str, client: OpenseaAccount) -> int:
        try:
            response = await client.get_collection_best_offer(item_id)
            return response["min_bid"]
        except Exception as error:
            logger.error(error)

    async def start_parsing(self, item_id: str):
        if len(self.tasks) < 140:
            if item_id in self.tasks:
                logger.info(f"Parsing for {item_id} is already running.")
                return
            self.stop_signals[item_id] = False
            task = asyncio.create_task(self.parse_item(item_id))
            self.tasks[item_id] = task
        else:
            pass

    async def stop_parsing(self, item_id: str):
        if item_id not in self.tasks:
            logger.info(f"No parsing task found for {item_id}.")
            return
        self.stop_signals[item_id] = True
        await self.tasks[item_id]  # Wait for the task to complete
        del self.tasks[item_id]
        del self.stop_signals[item_id]

    async def stop_all_parsing(self):
        for item_id in list(self.tasks.keys()):
            await self.stop_parsing(item_id)

    async def add_item(self, item_id: str):
        await self.start_parsing(item_id)

    async def remove_item(self, item_id: str):
        await self.stop_parsing(item_id)

    def get_item_value(self, item: str) -> Union[Dict[str, Any], float, str, None]:
        return self.slug_to_minbid.get(item)

    def set_item_value(self, item: str, value: Any) -> None:
        self.slug_to_minbid[item] = value


class InMemoryParser(OpenseaParser):
    def __init__(
            self,
            path_to_proxies: str = "proxies.txt",
    ):
        with open(path_to_proxies) as file:
            proxies = [i.replace("\n", "") for i in file.readlines()]

        def handler(loop, context):
            if context["message"] == "Event loop is closed":
                return
            loop.default_exception_handler(context)

        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.get_running_loop().set_exception_handler(handler)

        opensea_clients = [OpenseaAccount(Account.create().key.hex(), [proxy]) for proxy in proxies]
        super().__init__(opensea_clients)

        self.login_status = None

    async def submit_items(self, *item_slugs: str) -> None:
        for i in item_slugs:
            await self.add_item(i)


class PriceParserServer:
    def __init__(self, price_parser: InMemoryParser, port: int, host: str = '127.0.0.1'):
        self.host = host
        self.port = port
        self.price_parser = price_parser

    async def handle_client(self, reader, writer):
        try:
            data = await reader.read(2048)
            request = json.loads(data.decode())

            command = request.get('command')
            items = request.get('items')

            response = {"status": "success"}
            match command:
                case 'add_collections':
                    await self.price_parser.submit_items(*items)
                case 'get_prices':
                    prices = {i: self.price_parser.get_item_value(i) for i in items}
                    response['prices'] = prices
                case _:
                    response = {"status": "error", "message": "Unknown command."}

            writer.write(json.dumps(response).encode())
            await writer.drain()
        except Exception as e:
            error_response = {"status": "error", "message": str(e)}
            writer.write(json.dumps(error_response).encode())
            await writer.drain()
        finally:
            writer.close()

    async def start_server(self):
        async with await asyncio.start_server(self.handle_client, self.host, self.port) as server:
            await server.serve_forever()
