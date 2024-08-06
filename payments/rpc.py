import asyncio
import time
from functools import wraps

from web3 import Account, Web3
from web3.eth import AsyncEth

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


class RPCRequestManager:
    def __init__(self, rpc_list: list[str]):
        self.w3_list = [Web3(
            Web3.AsyncHTTPProvider(
                url,
                request_kwargs={"ssl": False}
            ),
            modules={"eth": (AsyncEth,)},
            middlewares=[]
        ) for url in rpc_list]

    async def get_first(self, func: callable, *args, **kwargs):
        tasks = [asyncio.create_task(func(w3, *args, **kwargs)) for w3 in self.w3_list]
        finished, unfinished = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

        for task in unfinished:
            task.cancel()
        if unfinished:
            await asyncio.wait(unfinished)

        for x in finished:
            return x.result()
