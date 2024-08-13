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
from encryption.system import encrypt_private_key, decrypt_private_key
from payments.db import DataBase
from payments.rpc import RPCRequestManager

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
        self._db = DataBase()

        self._nets = {
            net: {
                'w3': RPCRequestManager(net_config['rpcs']),
                'tokens': net_config['tokens']
            } for net, net_config in config.RPC_CONFIG.items()}

    async def get_temporary_wallet(self, uid: str | int):
        account = Account.create()
        wallet = Wallet(address=account.address, private_key=account.key.hex())

        encrypted = (await encrypt_private_key(wallet.private_key)).decode()
        self._db.insert(uid=uid, address=wallet.address, private_key=encrypted)
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
                results = await asyncio.gather(*(self.fetch_balance(address=address, net=net) for net in self._nets.keys()))

                for result in results:
                    for resp in result:
                        resp['balance'] = 240 # todo: DELETE IN PRODUCTION
                        if resp["balance"] > 0:
                            self._db.set_paid(wallet.address, chain_id=resp["chain_id"], paid=resp["balance"])
                            loguru.logger.info(
                                f'Found balance for: {address} in chain with number {resp["chain_id"]} | balance: {resp["balance"]}')
                            return resp

                await asyncio.sleep(10)
            except Exception as _err:
                logger.exception(_err)
                await asyncio.sleep(10)

        loguru.logger.info(f'Nothin was found at address: {address}')

    async def fetch_balance(self, address: str, net: str):
        if net not in self._nets.keys():
            raise KeyError(f'Net {net} is not presented in RPC_CONFIG')
        else:
            rpc_manager = self._nets[net]['w3']
            tokens = self._nets[net]['tokens']
        return await rpc_manager.get_first(self._fetch_balance, address=address, token_addresses=tokens)

    async def fetch_bot_balance(self, address: str):
        return await self._nets['ethereum']['w3'].get_first(self._fetch_bot_balance, address=address)

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
    async def _fetch_bot_balance(w3: Web3, address: str) -> dict:
        if address == '':
            raise ValueError(f'Address `{address}` is empty.')

        address = Web3.to_checksum_address(address)
        weth_balance = await PaymentsManager._fetch_balance(
            w3, address, ["0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"]
        )
        eth_balance = float(Web3.from_wei(await w3.eth.get_balance(address), "ether"))
        return {
            "weth": weth_balance[0]["balance"],
            "eth": eth_balance
        }


manager = PaymentsManager()
