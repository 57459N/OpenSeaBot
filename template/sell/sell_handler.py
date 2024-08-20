import asyncio
import json
import time
from web3 import Web3
from eth_account import Account
from web3.eth import AsyncEth
from eth_abi.abi import encode
from loguru import logger


from utils.telegram import TelegramLogger
from bidder.opensea_pro.client import OpenseaProAccount, ABI
from utils.web_utils import gas_price_checker
from collections_parser.parser import FETCH_FLOOR_PRICE
from utils.database import get_data_from_db


async def determine_sale_price(prices, min_difference_percent=5, margin=0.0001*10**18):

    if len(prices) < 2:
        return prices[0] - margin

    difference_percent = ((prices[1] - prices[0]) / prices[0]) * 100

    if difference_percent > min_difference_percent:
        return prices[1] - margin
    else:
        return prices[0] - margin

class SellAccount(TelegramLogger):
    def __init__(self, bot_token: str, user_id: int, secret_key: str, proxies: list, provider_link: str, max_gwei: float, max_dump_percent: float) -> None:
        super().__init__(bot_token, user_id)

        self.opensea_pro = OpenseaProAccount(secret_key, proxies)
        self.w3 = Web3(
            Web3.AsyncHTTPProvider(
                provider_link, request_kwargs={"ssl": False}
            ),
            modules={"eth": (AsyncEth,)},
            middlewares=[]
        )
        self.max_gas_price = Web3.to_wei(max_gwei, 'gwei')
        self.max_dump_percent = max_dump_percent

    @gas_price_checker
    async def check_approved(self, items: list) -> None:
        nonce = await self.w3.eth.get_transaction_count(self.opensea_pro.address)

        transactions = []

        for item in items:
            contract = self.w3.eth.contract(Web3.to_checksum_address(item["address"]), abi=ABI)

            if not (await contract.functions.isApprovedForAll(self.opensea_pro.address, "0x1E0049783F008A0085193E00003D00cd54003c71").call()):
                current_gas_price = await self.w3.eth.gas_price * 1.3

                transactions.append(
                    {
                        'chainId': 1, 
                        'nonce': nonce,  
                        'from': self.opensea_pro.address, 
                        "value": 0,
                        "data": "0xa22cb465" + encode(
                            ["address", "bool"],
                            ["0x1E0049783F008A0085193E00003D00cd54003c71", True]
                        ).hex(),
                        "to": Web3.to_checksum_address(item["address"]),
                        "maxPriorityFeePerGas": Web3.to_wei(0.0525252, "gwei"),
                        "maxFeePerGas": int(current_gas_price),
                        "gas": 205252
                    }
                )

                nonce += 1

        if len(transactions) > 0:
            logger.info(f'Created approve data for: {len(transactions)} transactions')

        return [self.opensea_pro.account.sign_transaction(tx) for tx in transactions]
    
    async def fetch_item_listings(self, slug: str) -> dict:
        item_listings = await self.opensea_pro.request(
            "get",
            "https://api.pro.opensea.io/collections%2F" + slug + "%2Fassets",
            params=FETCH_FLOOR_PRICE
        )

        some_listings = [int(x["currentEthPrice"]) for x in item_listings["data"] if x["maker"] != self.opensea_pro.address.lower()]

        my_price = 0
        for i in item_listings["data"]:
            if i["maker"] == self.opensea_pro.address.lower():
                my_price = int(round((i["currentEthPrice"] * 0.995) / 10**18, 4) * 10**18)

        return {
            "floor_price": int(await determine_sale_price(some_listings[:2])),
            "item_page": item_listings["data"],
            "my_price": my_price
        }
    
    
    async def proccess_listings(self, item_assets: list) -> None:
        for item in item_assets:
            try:
                contract_address = item["contract"]["address"]
                token_id = int(item["token_id"])
                price_data = await self.fetch_item_listings(item["collection_slug"])
                my_price = price_data["my_price"]

                if my_price != price_data["floor_price"]:
                    response = await self.proccess_seaport_sell(
                        token_id=token_id,
                        token_address=contract_address,
                        price=price_data["floor_price"],
                        assets_data=item_assets
                    )
                    #logger.debug(f'Sell response for item: {token_id} | {response}')
                    
            except Exception as error:
                logger.error(f'Failed to proccess listing: {item["token_id"]} | {error}')

    async def proccess_seaport_sell(self, token_id: int, token_address: str, price: int, assets_data: list) -> dict:
        async def validate(buy_price: int = 0) -> int:
            for i in assets_data:
                if i["token_id"] == str(token_id) and i["contract"]["address"] == token_address.lower():
                    buy_price = i["last_sale"]["price"]["amount"]

            max_dump_price = (buy_price / 100) * (100 - self.max_dump_percent)
            return price >= max_dump_price
        
        if len(self.opensea_pro.auth_token) < 5:
            await self.opensea_pro.login()
        
        if await validate():
            response = await self.opensea_pro.seaport_selling(
                {
                    "identifierOrCriteria": [token_id],
                    "price": price,
                    "token_address": token_address
                }
            )

            return response

        else:
            logger.debug(f'Cant dump item couse max item dump percent is too low..')

        
    async def manage_listings(self) -> None:
        data = (await self.opensea_pro.get_account_assets())["data"]["owned_assets"]
        await self.proccess_listings([item["asset"] for item in data])
        

    async def approve_items(self) -> None:
        account_items = (await self.opensea_pro.get_account_portfolio(simple_resp=True))["data"]["collections"]
        approved_transactions = await self.check_approved(
            [item for item in account_items if item["numItemsOwned"] > item["numItemsListed"]]
        )
        tasks = [
            self.w3.eth.send_raw_transaction(signed_txn.rawTransaction) for signed_txn in approved_transactions
        ]
        responses = await asyncio.gather(*tasks)


        if len(responses) != 0:
            links = "".join(f"<a href='https://etherscan.io/tx/{Web3.to_hex(i)}'>Etherscan</a></i>\n" for i in responses)
            message = f'<b>❗️New action❗️</b>\n\n<i>Approved new NFTs for selling:</i>\n{links}'
            asyncio.create_task(self.send_message(message))


    async def infinity_handler(self) -> None:
        logger.info(f'OpenseaPro sellings handler was started!')
        while (await get_data_from_db()):
            try:
                tasks = [self.manage_listings(), self.approve_items()]
                await asyncio.gather(*tasks)

                await asyncio.sleep(30)
            
            except Exception as _err:
                logger.exception(_err)