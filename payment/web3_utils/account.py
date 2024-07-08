from eth_account import Account
import time
from loguru import logger
from web3 import Web3
from web3.eth import AsyncEth
import asyncio

abi = [
    {
        "inputs": [{"internalType":"address","name":"account","type":"address"}],
        "name": "balanceOf",
        "outputs": [{"internalType":"uint256","name":"","type":"uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [{"internalType":"uint256","name":"","type":"uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]


async def generate_account() -> dict:
    account = Account.create()

    return {
        "address": account.address,
        "secret": account.key.hex()
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
                balance = round(balance / 10**decimals, 2)

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
                        logger.info(f'Found balance for: {address} in chain with number {resp["chain_id"]} | balance: {resp["balance"]}')
                        return resp
            
            logger.info(f'Nothin was found at address: {address}')
            await asyncio.sleep(10)

        except Exception as _err:
            logger.exception(_err)
            await asyncio.sleep(10)
