from eth_account import Account
from bidder.opensea.client import OpenseaAccount
from bidder.opensea_pro.client import OpenseaProAccount, round_to_multiple
from loguru import logger
import time
import asyncio
import random
from utils.database import *
from utils.utils import load_data


class Client:
    def __init__(self, settings: dict) -> None:
        private_key = settings["private_key"]
        main_proxies = settings["settings"]["proxies"]["main"]
        parse_proxies = settings["settings"]["proxies"]["parse_proxies"]

        self.opensea = OpenseaAccount(private_key, main_proxies)
        self.opensea_pro = OpenseaProAccount(private_key, main_proxies)
        self.fetch_opensea_sessions = [OpenseaAccount(Account.create().key.hex(), [proxy]) for proxy in parse_proxies]
        self.fetch_opensea_pro_sessions = [OpenseaProAccount(Account.create().key.hex(), [proxy]) for proxy in parse_proxies]
        self.config = settings["settings"]

        self.portfolio = {}


    async def close_all_sessions(self) -> None:
        for i in self.fetch_opensea_sessions:
            await i.close_session()
        
        for i in self.fetch_opensea_pro_sessions:
            await i.close_session()

        await self.opensea.close_session()
        await self.opensea_pro.close_session()
    
    async def get_collections_to_fetch(self):
        return [
            item for item in self.config["collections"] if item not in list(self.portfolio.keys())
        ]


    async def portfolio_fetcher(self) -> None:
        while (await get_data_from_db()):
            try:
                self.portfolio = await self.opensea_pro.get_account_portfolio()
                logger.info(f'Portfolio fetched. Items owned: {len(self.portfolio.keys())}')
                self.config = await get_settings_data_from_db()

                await asyncio.sleep(1)

            except Exception as error:
                logger.error(f'Failed to update portfolio: {error}')


    async def fetch_all_items(self, items: list, pro: bool = False):
        tasks = []

        while len(items) != 0:
            random.shuffle(self.fetch_opensea_sessions)
            random.shuffle(self.fetch_opensea_pro_sessions)

            if not pro:
                for _session in self.fetch_opensea_sessions:
                    _session: OpenseaAccount

                    if len(items) > 0: 
                        tasks.append(
                            _session.safe_executor(
                                _session.get_collection_best_offer,
                                items.pop()
                            )
                        )
            else:
                for session in self.fetch_opensea_pro_sessions:
                    session: OpenseaProAccount

                    if len(items) > 0: 
                        tasks.append(
                            session.safe_executor(
                                session.fetch_collection,
                                items.pop()
                            )
                        )
        
        responses = await asyncio.gather(*tasks)
        return [resp for resp in responses if resp]
    
    async def login_to_fetch_sessions(self) -> None:
        tasks = [
            account.login() for account in self.fetch_opensea_sessions
        ]
        await asyncio.gather(*tasks)
    
    async def get_change_list_from_opensea(self, all_items: list, current_orders: dict) -> list:
        profit = self.config["profit"] / 100

        current_prices = await self.fetch_all_items([i for i in all_items])
        change_items = []

        #input(json.dumps(current_prices, indent=4))

        for item in current_prices:
            my_order_price = float(current_orders.get(item["slug"]))

            best_bid_price = item["min_bid"]
            floor_price = item["floor_price"]

            if item["sales_ratio_percent"] > 60:

                if my_order_price < best_bid_price:
                    if floor_price * (1-profit) > best_bid_price + 0.001:
                        change_items.append(
                            {
                                "name": item["slug"], 
                                "price": round(best_bid_price + 0.0001, 4), 
                                "address": item["address"]
                            }
                        )
                        #logger.info(f'[{item["slug"]}] will try to make re-bid with new price: {round(best_bid_price + 0.0001, 4)}')
                    else:
                        logger.info(f'[{item["slug"]}] is lower than best bid price: {best_bid_price}, but profit is too low: {floor_price}')
                    
                elif best_bid_price == my_order_price:
                    pass
                    #logger.info(f'[{item["slug"]}] selling this item with top price: {my_order_price}')
        
        return change_items

    async def get_change_list_from_opensea_pro(self, all_items: list, current_orders: dict) -> list:
        profit = self.config["profit"] / 100

        current_prices = await self.fetch_all_items([i for i in all_items], pro=True)
        change_items = []

        #input(json.dumps(current_prices, indent=4))

        for item in current_prices:
            my_order_price = float(current_orders.get(item["slug"]))

            best_bid_price = float(item["best_bid"]["price"] / 10**18)
            second_bid_price = float(min(item["orders"], key=lambda x: x["price"])["price"] / 10**18)
            floor_price = float(item["floor_price"] / 10**18)

            #logger.debug(f'[{item["slug"]}] {my_order_price} - {best_bid_price} - {second_bid_price}')

            if my_order_price < best_bid_price:
                if floor_price * (1-profit) > best_bid_price + 0.001:
                    change_items.append(
                        {
                            "name": item["slug"], 
                            "price": round(best_bid_price + 0.0001, 4), 
                            "address": item["address"]
                        }
                    )
                    #logger.info(f'[{item["slug"]}] will try to make re-bid with new price: {round(best_bid_price + 0.0001, 4)}')
                else:
                    pass
                    #logger.info(f'[{item["slug"]}] is lower than best bid price: {best_bid_price}, but profit is too low')
                
            elif best_bid_price == my_order_price:
                if second_bid_price + 0.001 < my_order_price:
                    if floor_price * (1-profit) > second_bid_price + 0.001:
                        change_items.append(
                            {
                                "name": item["slug"], 
                                "price": round(second_bid_price + 0.0001, 4), 
                                "address": item["address"]
                            }
                        )
                        #logger.info(f'[{item["slug"]}] will try to reduce the price becouse second order is lower then top. new price: {round(second_bid_price + 0.0001, 4)} | old: {my_order_price}')

        return change_items


    async def work(self, config: list) -> None:
        await self.opensea.close_all_active_offers()
        await self.login_to_fetch_sessions()

        current_orders = {}
        for item in config["collections"]:
            current_orders.update({item: 0})


        last_time_dump_items = 0
        time_to_relogin = time.time() + 120
        time_to_die = time.time() + 3600


        while (await get_data_from_db()):
            data = {}

            if time_to_relogin < time.time():
                await self.opensea.get_collection_best_offer("pixeladymaker")
                time_to_relogin = time.time() + 120
                
            if time.time() > time_to_die:
                return
                
            start_time = time.time()

            collections = await self.get_collections_to_fetch()

            if last_time_dump_items + 60 < time.time():
                change_list = await self.get_change_list_from_opensea_pro(collections, current_orders)
                logger.debug(f'Fetched items from opensea pro')
                last_time_dump_items = time.time()

                for i in self.portfolio.keys():
                    data.update(
                        {
                            i: 9999
                        }
                    )

            else:
                change_list = await self.get_change_list_from_opensea(collections, current_orders)

            for i in change_list:
                data.update(
                    {
                        i["name"]: i["price"]
                    }
                )

            logger.success(f'End parsing with: {time.time() - start_time} seconds')

            #logger.debug(f'Change list: {json.dumps(change_list, indent=2)}')

            items_in_batch = 10
            last_changed_time = 0

            closed_items = False
            logger.debug(f'Have change list for: {len(change_list)} items')

            while len(change_list) != 0:
                if time.time() > last_changed_time + 1:

                    tasks = []
                    for _ in range(items_in_batch):
                        if len(change_list) != 0:
                            work_item = change_list.pop()

                            tasks.append(
                                self.opensea.safe_executor(
                                    self.opensea_pro.seaport_offer, 
                                    work_item["name"], 0.5, work_item["address"], int(work_item["price"] * 1e18)
                                )
                            )
                            if closed_items is False:
                                tasks.append(
                                    self.opensea.safe_executor(
                                        self.opensea.close_collection_worst_orders, data
                                    )
                                )
                                closed_items = True


                            current_orders[work_item["name"]] = work_item["price"]

                    last_changed_time = time.time()
                    await asyncio.gather(*tasks)
                    logger.success(f'Proccessed the batch')


async def work_client() -> None:
    config = await load_data()
    account = Client(config)
    asyncio.create_task(account.portfolio_fetcher())

    while (await get_data_from_db()):
        try:
            await account.opensea.login()
            await account.opensea_pro.login()

            tasks = [
                account.opensea.safe_executor(
                    account.work, config["settings"]
                )
            ]
            
            await asyncio.gather(*tasks)

        except Exception as error:
            logger.error(f'Main: {error}')
            await account.close_all_sessions()
        
        await asyncio.sleep(30)
