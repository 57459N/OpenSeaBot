from loguru import logger
from web3 import Web3
import asyncio


async def check_gas_price(provider: Web3) -> int:
    try:
        current_gas = await provider.eth.gas_price
        return current_gas

    except Exception as _err:
        logger.exception(_err)
        return Web3.to_wei(999, "gwei")


def gas_price_checker(func):
    async def wrapper(self, *args, **kwargs):
        while True:
            current_gas_price = await check_gas_price(self.w3)
            if current_gas_price <= self.max_gas_price:
                return await func(self, *args, **kwargs)
            else:
                print(f"Текущая цена газа {current_gas_price} выше допустимой {self.max_gas_price}, ждем 20 секунд...")
                await asyncio.sleep(20)
    return wrapper