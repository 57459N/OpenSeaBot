import asyncio

from utils.database import init_all_dbs
from utils.paths import *
from utils.utils import *

from collections_parser.parser import collections_update_handler, collections_prices_handler
from utils.encode_secret_key import *
from bidder.bidder_client import work_client


async def main():
    tasks = [
        asyncio.create_task(collections_update_handler()),
        asyncio.create_task(collections_prices_handler()),
        # asyncio.create_task(work_client())
        #
    ]

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    # print(asyncio.run(load_data()))
    asyncio.run(main())
