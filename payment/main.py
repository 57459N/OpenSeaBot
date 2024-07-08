from web3_utils.account import *
import asyncio


async def main() -> None:
    account = await generate_account()

    await check_payment_handler(
        config={
            "ethereum": {
                "rpc": "https://1rpc.io/eth",
                "tokens": [
                    "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                    "0xdAC17F958D2ee523a2206206994597C13D831ec7"
                ]
            }
        },
        timeout=60,
        _address=account["address"]
    )


if __name__ == "__main__":
    asyncio.run(main())


