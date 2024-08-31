import asyncio
import json
from bidder.opensea_pro.client import OpenseaProAccount, ABI
import time
from web3 import Web3
from eth_account import Account
from web3.eth import AsyncEth
from eth_abi.abi import encode
from loguru import logger

from utils.telegram import TelegramLogger
from utils.database import get_data_from_db
from utils.web_utils import gas_price_checker

WETH_CONTRACT = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
OPENSEA_CONTRACT = "0x1E0049783F008A0085193E00003D00cd54003c71"
APPROVE_AMOUNT = 2**256 - 1


class WorkAccount(TelegramLogger):
    def __init__(self, bot_token: str, user_id: int, secret_key: str, proxies: list, provider_link: str, max_gwei: float) -> None:
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

        self.MIN_ETH_BALANCE = 0.01 * 10**18
        self.SAVE_ETH_BALANCE = 0.01 * 10**18

        self.last_block_data = (0, False)

    @gas_price_checker
    async def wrap_handler(self, balance: int) -> None:
        nonce = await self.w3.eth.get_transaction_count(self.opensea_pro.address)
        gas_price = (await self.w3.eth.gas_price) * 1.3
        tx_fee = gas_price * 77777
        deposit_amount = int(balance - tx_fee - self.SAVE_ETH_BALANCE) + 52

        current_block = await self.w3.eth.block_number

        if deposit_amount > 0:
            transaction = {
                "from"    : self.opensea_pro.address,
                "to"      : WETH_CONTRACT,
                "nonce"   : nonce,
                "chainId" : 1,
                "value"   : deposit_amount,
                "gas"     : 77777,
                "maxPriorityFeePerGas": Web3.to_wei(0.1, "gwei"),
                "maxFeePerGas": int(gas_price),
                "data": "0xd0e30db0",
                "type": 2
            }

            signed_txn = self.opensea_pro.account.sign_transaction(transaction)
            tx_hash = (await self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)).hex()
            self.last_block_data = (current_block, True)

            message = f"""<b>❗️New action❗️</b>

<i>Deposit {round(deposit_amount / 10**18, 4)} eth to WETH | <a href='https://etherscan.io/tx/{tx_hash}'>Etherscan</a></i>"""

            asyncio.create_task(self.send_message(message))
            await asyncio.sleep(120)

    async def wrap_eth(self) -> None:
        balance = await self.w3.eth.get_balance(self.opensea_pro.address)
        if balance > self.MIN_ETH_BALANCE:
            await self.wrap_handler(balance)


    async def is_opensea_approved(self) -> bool:
        contract = self.w3.eth.contract(WETH_CONTRACT, abi=ABI)

        allowance = await contract.functions.allowance(
            self.opensea_pro.address, OPENSEA_CONTRACT
        ).call()
        return allowance > 10 * 10**18
    

    @gas_price_checker
    async def approve_handler(self) -> None:
        nonce = await self.w3.eth.get_transaction_count(self.opensea_pro.address)
        gas_price = (await self.w3.eth.gas_price) * 1.3
        tx_fee = gas_price * 77777

        balance = await self.w3.eth.get_balance(self.opensea_pro.address)
        current_block = await self.w3.eth.block_number

        if self.last_block_data[0] == current_block: nonce += 1

        if balance > tx_fee:
            transaction = {
                "from"    : self.opensea_pro.address,
                "to"      : WETH_CONTRACT,
                "nonce"   : nonce,
                "chainId" : 1,
                "value"   : 0,
                "gas"     : 77777,
                "maxPriorityFeePerGas": Web3.to_wei(0.1, "gwei"),
                "maxFeePerGas": int(gas_price),
                "data": "0x095ea7b3" + encode(
                    ["address", "uint256"], [OPENSEA_CONTRACT, APPROVE_AMOUNT]
                ).hex(),
                "type": 2
            }

            signed_txn = self.opensea_pro.account.sign_transaction(transaction)
            tx_hash = (await self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)).hex()

            self.last_block_data = (current_block, True)

            message = f"""❗️<b>New action</b>❗️

<i>Approved all WETH for Opensea | <a href='https://etherscan.io/tx/{tx_hash}'>Etherscan</a></i>"""

            asyncio.create_task(self.send_message(message))

            await asyncio.sleep(120)
    
    async def approve_opensea(self) -> None:
        if not await self.is_opensea_approved():
            await self.approve_handler()


    async def infinity_handler(self):
        logger.info(f'Opensea approvals handler was started! ')
        while (await get_data_from_db()):
            try:
                tasks = [self.approve_opensea(), self.wrap_eth()]
                await asyncio.gather(*tasks)

                await asyncio.sleep(60)
            
            except Exception as _err:
                logger.exception(_err)

