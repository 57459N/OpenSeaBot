from redis_client.redis_client import RedisManager
import asyncio
from redis_client.opensea.client import OpenseaAccount
from loguru import logger
from eth_account import Account

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
        logger.info(f'Sessions handler was runned! ')
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
        self.redis = RedisManager()
        self.tasks = {}
        self.stop_signals = {}
        self.opensea_accounts = {}

    async def parse_item(self, item_id: str):
        redis_client = await self.redis.get_new_client()
        while not self.stop_signals.get(item_id, False):
            client = self.get()
            price = await self.fetch_price(item_id, client)
            if price:
                logger.success(f'{item_id}:{price}')
                await self.redis.set_item_value(redis_client, item_id, {"slug": item_id, "min_bid": price})

    async def fetch_price(self, item_id: str, client: OpenseaAccount) -> int:
        try:
            response = await client.get_collection_best_offer(item_id)
            return response["min_bid"]
        except Exception as error:
            logger.error(error)
        

    async def start_parsing(self, item_id: str):
        if item_id in self.tasks:
            logger.info(f"Parsing for {item_id} is already running.")
            return
        self.stop_signals[item_id] = False
        task = asyncio.create_task(self.parse_item(item_id))
        self.tasks[item_id] = task

    async def stop_parsing(self, item_id: str):
        if item_id not in self.tasks:
            logger.info(f"No parsing task found for {item_id}.")
            return
        self.stop_signals[item_id] = True
        await self.tasks[item_id]  # Ждём завершения задачи
        del self.tasks[item_id]
        del self.stop_signals[item_id]

    async def stop_all_parsing(self):
        for item_id in list(self.tasks.keys()):
            await self.stop_parsing(item_id)

    async def add_item(self, item_id: str):
        await self.start_parsing(item_id)

    async def remove_item(self, item_id: str):
        await self.stop_parsing(item_id)


class RedisParser(OpenseaParser):
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

    async def submit_items(self, item_slugs: list) -> None:
        if not self.login_status:
            tasks = [account.safe_executor(account.login) for account in self.clients]
            await asyncio.gather(*tasks)
            asyncio.create_task(self.sessions_handler())
            self.login_status = True

        for i in item_slugs: await self.add_item(i)