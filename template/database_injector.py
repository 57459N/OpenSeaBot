import asyncio
from utils.database import *

with open('proxies.txt') as file:
    proxies = [row.strip() for row in open("proxies.txt")]

async def main():
    await change_work_statement({"work_statement": True}) # True - софт пашет | False - останавливается

    await update_settings_database(
        {
            "collections_parser": {
                "min_price": 0.1,
                "max_price": 2,
                "min_one_day_sellings": 10,
                "min_one_day_volume": 5,
                "offer_difference_percent": 2,
            },
            "profit": 7,
            #"collections": [ # при collections_update_handler обновляется самостоятельно
            #    "fuck1",
            #    "fuck2",
            #    "fuck3"
            #],
            "proxies": {
                "main": [
                    'igp1040518:mDss0nxNfp@77.83.1.144:7951', 
                    'igp1040518:mDss0nxNfp@77.83.1.170:7951'
                ],
                "parse_proxies": proxies # из файла proxies.txt
            }
        }
    )


if __name__ == "__main__":
    asyncio.run(main())
