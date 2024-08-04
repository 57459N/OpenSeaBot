import asyncio

from utils.database import init_all_dbs, change_work_statement, update_settings_database


async def main():
    await init_all_dbs()
    await change_work_statement({"work_statement": False})
    await update_settings_database({
        "collections_parser": {
            "min_price": 0.1,
            "max_price": 2,
            "min_one_day_sellings": 10,
            "min_one_day_volume": 5,
            "offer_difference_percent": 2,
        },
        "profit": 7,
    })


if __name__ == "__main__":
    asyncio.run(main())
