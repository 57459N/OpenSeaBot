import time
import asyncio
from bidder.opensea.client import OpenseaAccount
from bidder.opensea_pro.client import OpenseaProAccount
from loguru import logger
from utils.database import get_data_from_db, get_settings_data_from_db
from utils.price_manager import price_requests
from bidder.opensea.utils import fetch_current_prices
from bidder.opensea_pro.utils import fetch_pro_current_prices
from utils.utils import retry

class ClientSessions:
    def __init__(self, private_key: str, proxies: list, config: dict) -> None:
        self.private_key = private_key
        self.proxies = proxies
        self.config = config
        self.opensea = OpenseaAccount(private_key, proxies)
        self.opensea_pro = OpenseaProAccount(private_key, proxies)
        self.portfolio = {}

    @retry(max_retries=1)
    async def close_sessions(self) -> None:
        await asyncio.gather(self.opensea.close_session(), self.opensea_pro.close_session())

    @retry(infinity=True, timing=1, catch_exception=True)
    async def executor(self, function, *args):
        await function(*args)

    @retry(infinity=True, timing=10)
    async def sessions_handler(self) -> None:
        while await get_data_from_db():
            await asyncio.gather(self.opensea.login(), self.opensea_pro.login())
            await self.executor(self.opensea.close_all_active_offers)
            self.current_orders = {item: 0 for item in self.config.get("collections", [])}

            await asyncio.sleep(500)

    async def portfolio_fetcher(self) -> None:
        while await get_data_from_db():
            try:
                self.portfolio = await self.opensea_pro.get_account_portfolio()
                logger.info(f'Portfolio fetched. Items owned: {len(self.portfolio)}')
                self.config = await get_settings_data_from_db()
                await asyncio.sleep(1)
            except Exception as error:
                logger.error(f'Failed to update portfolio: {error}')
                await self.opensea_pro.login()

class BidderClient(ClientSessions):
    def __init__(self, private_key: str, proxies: list, config: dict) -> None:
        super().__init__(private_key, proxies, config)
        self.handlers_status = False
        self.last_fetch_from_opensea_pro = 0
        self.current_orders = {}

        self.items_in_batch = 10

    async def fetch_market_data(self, collections: list, pro: bool, profit: float) -> list:

        collections  = [i.replace("_pro", "") for i in collections]# fastfix
        response = await price_requests.get_items_values(*collections)
        fetch_function = fetch_current_prices if pro else fetch_current_prices
        return await fetch_function(profit, response, self.current_orders)

    async def process_batch_orders(self, change_list: list, close_data: dict) -> None:
        last_changed_time = 0
        closed_items = False
        if len(change_list) > 0:
            logger.debug(f'Have change list for: {len(change_list)} items')

        while change_list:
            if time.time() > last_changed_time + 1:
                for _ in range(min(self.items_in_batch, len(change_list))):
                    work_item = change_list.pop()
                    
                    asyncio.create_task(
                        self.opensea.safe_executor(
                            self.opensea_pro.seaport_offer, 
                            work_item["name"], 0.5, work_item["address"], int(work_item["price"] * 1e18)
                        )
                    )
                    
                    if not closed_items:
                        asyncio.create_task(self.opensea.safe_executor(self.opensea.close_collection_worst_orders, close_data))
                        closed_items = True
                    self.current_orders[work_item["name"]] = work_item["price"]

                last_changed_time = time.time()
                logger.success('Processed the batch')

    async def get_change_list(self, pro: bool = False) -> list:
        collections = [
            item for item in self.config["collections"] if item not in self.portfolio
        ]
        if self.last_fetch_from_opensea_pro + 60 < time.time():
            pro = True
            collections = [f"{item}_pro" for item in collections]

        profit = self.config["profit"] / 100
        change_list = await self.fetch_market_data(collections, pro, profit)
        return {i["name"]: i["price"] for i in change_list}, change_list

    @retry(infinity=True, timing=1)
    async def start(self) -> None:
        if not self.handlers_status:
            asyncio.create_task(self.portfolio_fetcher())
            asyncio.create_task(self.sessions_handler())
            self.handlers_status = True
            await asyncio.sleep(20)

        while await get_data_from_db():
            close_data, change_list = await self.get_change_list()
            await self.process_batch_orders(change_list, close_data)
