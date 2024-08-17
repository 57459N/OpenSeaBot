import asyncio
import pathlib
import sys

from bidder.bidder_client import BidderClient
from checkers.opensea_approval import WorkAccount
from collections_parser.parser import collections_update_handler, collections_prices_handler
from utils.database import update_settings_database
from utils.utils import load_data

from sell.sell_handler import SellAccount

sys.path.append(str(pathlib.Path(__file__).parent.parent.parent.parent))
from config import BOT_API_TOKEN, RPC_CONFIG, redis_client


async def start_program(app=None):
    # todo: UNCOMMENT ON PRODUCTION
    asyncio.create_task(collections_update_handler(redis_client))
    asyncio.create_task(collections_prices_handler())

    account_data = await load_data()

    asyncio.create_task(
        WorkAccount(
            bot_token=BOT_API_TOKEN,
            user_id=account_data["user_id"],
            secret_key=account_data["private_key"],
            proxies=[],
            provider_link=RPC_CONFIG["ethereum"]["rpcs"][0],
            max_gwei=50  # todo: user may change it by himself
        ).infinity_handler()
    )

    with open('proxies.txt') as file:
        proxies = [row.strip() for row in file.readlines()]
    main_proxies = proxies[:2]

    asyncio.create_task(
        SellAccount(
            bot_token=BOT_API_TOKEN,
            user_id=account_data["user_id"],
            secret_key=account_data["private_key"],
            proxies=main_proxies,
            provider_link=RPC_CONFIG["ethereum"]["rpcs"][0],
            max_gwei=50,  # todo: user may change it by himself
            max_dump_percent=1
        ).infinity_handler()
    )

    asyncio.create_task(
        BidderClient(
            secret_key=account_data["private_key"], 
            proxies=main_proxies, 
            config=account_data["settings"]
        ).start()
    )

async def set_proxies(app=None):
    with open('proxies.txt') as file:
        proxies = [row.strip() for row in file.readlines()]
    main_proxies = proxies[:2]
    proxies = proxies[2:]
    await update_settings_database(
        {
            "proxies": {
                "main": main_proxies,
                "parse_proxies": proxies  # из файла proxies.txt
            }
        }
    )

