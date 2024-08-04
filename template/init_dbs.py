import asyncio

from utils.database import init_all_dbs


async def main():
    await init_all_dbs()


if __name__ == "__main__":
    asyncio.run(main())
