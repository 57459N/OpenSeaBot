import dataclasses
from datetime import datetime, timedelta

import loguru
from eth_account import Account
import time
from loguru import logger
from web3 import Web3
from web3.eth import AsyncEth
import asyncio

import config
from db import DataBase
from rpc import RPCRequestManager

abi = [
    {
        "inputs": [{"internalType": "address", "name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]


@dataclasses.dataclass
class Wallet:
    address: str
    expires: datetime
    private_key: str
    paid: bool

    def __init__(self, address: str, private_key: str, expires: datetime = None, paid: bool = False):
        self.address = address
        self.paid = paid
        self.private_key = private_key
        if expires is None:
            self.expires = datetime.now() + timedelta(seconds=config.TEMP_WALLET_EXPIRE_SECONDS)
        else:
            self.expires = expires

    def __bool__(self):
        return not self.paid and self.expires > datetime.now()


class PaymentsManager:
    def __init__(self):
        self.db = DataBase()
        self.rpcs = RPCRequestManager()

    async def get_temporary_wallet(self, uid: str | int):
        account = Account.create()
        wallet = Wallet(address=account.address, private_key=account.key.hex())

        await self.db.insert(uid, wallet.address, wallet.private_key, False)
        return wallet

    @staticmethod
    async def generate_account():
        account = Account.create()

        return {
            "address": account.address,
            "secret": account.key.hex()
        }

    async def handle_payment(self, wallet: Wallet):
        address = Web3.to_checksum_address(wallet.address)

        while wallet:
            try:
                result = await self.fetch_balance(
                    address=address,
                    token_addresses=["0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                                     "0xdAC17F958D2ee523a2206206994597C13D831ec7"])

                for resp in result:
                    if resp["balance"] > 0:
                        loguru.logger.info(
                            f'Found balance for: {address} in chain with number {resp["chain_id"]} | balance: {resp["balance"]}')
                        return resp

                loguru.logger.info(f'Nothin was found at address: {address}')
                await asyncio.sleep(10)

            except Exception as _err:
                logger.exception(_err)
                await asyncio.sleep(10)

    async def fetch_balance(self, address: str, token_addresses: list[str]):
        return await self.rpcs.get_first(self._fetch_balance, address=address, token_addresses=token_addresses)

    async def fetch_bot_balance(self, address: str):
        return await self.rpcs.get_first(self._fetch_bot_balance, _address=address)

    @staticmethod
    async def _fetch_balance(w3: Web3, address: str, token_addresses: list) -> list[dict[str, int]]:
        results = []
        for token in token_addresses:
            try:
                contract = w3.eth.contract(Web3.to_checksum_address(token), abi=abi)
                balance = await contract.functions.balanceOf(address).call()

                if balance > 0:
                    decimals = await contract.functions.decimals().call()
                    balance = round(balance / 10 ** decimals, 2)

                results.append(
                    {
                        "chain_id": await w3.eth.chain_id,
                        "balance": balance
                    }
                )
            except Exception as _err:
                results.append(
                    {
                        "chain_id": 0,
                        "balance": 0
                    }
                )
        return results

    @staticmethod
    async def _fetch_bot_balance(w3: Web3, _address: str) -> dict:
        address = Web3.to_checksum_address(_address)
        weth_balance = await RPCRequestManager._fetch_balance(
            w3, address, ["0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"]
        )
        eth_balance = float(Web3.from_wei(await w3.eth.get_balance(address), "ether"))
        return {
            "weth": weth_balance[0]["balance"],
            "eth": eth_balance
        }


async def connect_to_all_rpcs(config: dict) -> dict:
    result = {}
    for name in config.keys():
        result.update(
            {
                name: Web3(
                    Web3.AsyncHTTPProvider(
                        config[name]["rpc"],
                        request_kwargs={"ssl": False}
                    ),
                    modules={"eth": (AsyncEth,)},
                    middlewares=[]
                )
            }
        )
    return result


async def fetch_balance(w3: Web3, address: str, token_addresses: list) -> dict:
    results = []

    for token in token_addresses:
        try:
            contract = w3.eth.contract(Web3.to_checksum_address(token), abi=abi)
            balance = await contract.functions.balanceOf(address).call()

            if balance > 0:
                decimals = await contract.functions.decimals().call()
                balance = round(balance / 10 ** decimals, 2)

            results.append(
                {
                    "chain_id": await w3.eth.chain_id,
                    "balance": balance
                }
            )

        except Exception as _err:
            logger.exception(_err)
            results.append(
                {
                    "chain_id": 0,
                    "balance": 0
                }
            )

    return results


async def check_payment_handler(config: dict, _address: str, timeout: int = 60) -> dict:
    """
    config = {
        "arbitrum": {
            "rpc": "",
            "tokens": []
        },
        "ethereum": {
            "rpc": "",
            "tokens": []
        }
    }
    """
    address = Web3.to_checksum_address(_address)
    deadline = time.time() + timeout

    connected_rpcs = await connect_to_all_rpcs(config)

    while time.time() < deadline:
        try:
            tasks = [
                fetch_balance(
                    connected_rpcs[name], address, config[name]["tokens"]
                ) for name in config.keys()
            ]

            results = await asyncio.gather(*tasks)

            for batch_response in results:
                for resp in batch_response:
                    if resp["balance"] > 0:
                        logger.info(
                            f'Found balance for: {address} in chain with number {resp["chain_id"]} | balance: {resp["balance"]}')
                        return resp

            logger.info(f'Nothin was found at address: {address}')
            await asyncio.sleep(10)

        except Exception as _err:
            logger.exception(_err)
            await asyncio.sleep(10)


async def fetch_bot_balance(_address: str) -> dict:
    address = Web3.to_checksum_address(_address)

    w3 = Web3(
        Web3.AsyncHTTPProvider(
            "https://1rpc.io/eth",
            request_kwargs={"ssl": False}
        ),
        modules={"eth": (AsyncEth,)},
        middlewares=[]
    )

    weth_balance = await fetch_balance(
        w3, address, ["0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"]
    )

    eth_balance = float(Web3.from_wei(await w3.eth.get_balance(address), "ether"))

    return {
        "weth": weth_balance[0]["balance"],
        "eth": eth_balance
    }
