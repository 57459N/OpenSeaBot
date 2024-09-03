from requests_client.client import RequestsClient
from loguru import logger
from utils.database import *
import numpy as np
from utils.price_manager import price_requests

import traceback

PARAMS = {
    'fields[name]': '1',
    'fields[marketStats]': '1',
    'fields[addresses]': '1',
    'fields[address]': '1',
    'fields[revealPercentage]': '1',
    'fields[rarityRankingStatus]': '1',
    'fields[description]': '1',
    'fields[bannerImageUrl]': '1',
    'fields[imageUrl]': '1',
    'fields[sevenDayVolume]': '1',
    'fields[openSeaFees]': '1',
    'fields[fees]': '1',
    'fields[traits]': '1',
    'fields[standard]': '1',
    'fields[nftxFees]': '1',
    'fields[discordUrl]': '1',
    'fields[mediumUsername]': '1',
    'fields[createdAt]': '1',
    'fields[telegramUrl]': '1',
    'fields[twitterUsername]': '1',
    'fields[restrictedMarketplaces]': '1',
    'fields[stats.floor_price]': '1',
    'fields[stats.items_listed]': '1',
    'fields[stats.num_owners]': '1',
    'fields[stats.total_supply]': '1',
    'fields[stats.rolling_one_day_sales_change]': '1',
    'fields[stats.rolling_one_day_change]': '1',
    'fields[stats.rolling_one_day_volume]': '1',
    'fields[stats.rolling_one_day_sales]': '1',
    'fields[stats.farmerOwnedAssets]': '1',
    'fields[stats.floor_price_1m]': '1',
    'fields[stats.floor_price_5m]': '1',
    'fields[stats.floor_price_30m]': '1',
    'fields[stats.floor_price_1h]': '1',
    'fields[stats.floor_price_6h]': '1',
    'fields[stats.floor_price_1d]': '1',
    'fields[stats.floor_price_7d]': '1',
    'fields[stats.floor_price_30d]': '1',
    'fields[stats.floor_price_token_price]': '1',
    'fields[stats.floor_price_token_address]': '1',
    'fields[stats.floor_price_token_decimals]': '1',
    'fields[stats.floor_price_token_symbol]': '1',
    'fields[instagramUsername]': '1',
    'fields[totalSupply]': '1',
    'fields[wikiUrl]': '1',
    'fields[slug]': '1',
    'fields[createdDate]': '1',
    'fields[isVerified]': '1',
    'fields[ranksUpdatedAt]': '1',
    'fields[externalUrl]': '1',
    'fields[updatedAt]': '1',
    'fields[isOpenRarityEnabled]': '1',
    'fields[isCollectionOffersEnabled]': '1',
    'fields[isTraitOffersEnabled]': '1',
    'fields[mintData]': '1',
    'fields[disableMintOnOSPro]': '1',
    'fields[_id]': '0',
    'fields[isInactive]': '1',
    'fields[delistedReason]': '1',
    'fields[customData]': '1',
    'fields[chainName]': '1',
    'fields[indexingStatus]': '1',
}

FETCH_FLOOR_PRICE = {
    'offset': '0',
    'limit': '100',
    'filters[supportsWyvern]': 'true',
    'markets[]': [
        'seaport',
        'blur_v2',
        'blur',
    ],
    'sort[currentEthPrice]': 'asc',
    'status[]': 'buy_now',
}


class OpenseaProParser(RequestsClient):
    def __init__(self, proxy: list) -> None:
        super().__init__(proxy)

    async def fetch_pages(
            self,
            offset: int = 0,
            pages: int = 5,
            limit: int = 50,
            min_price: float = 0.1,
            max_price: float = 2
    ) -> list:
        result = {
            "items_fetched": 0,
            "data": []
        }

        for _ in range(pages):
            try:
                response = await self.request(
                    "get",
                    "https://api.pro.opensea.io/collections",
                    params={
                        'offset': str(offset),
                        'limit': str(limit),
                        'fields[createdDate]': '1',
                        'fields[createdAt]': '1',
                        'fields[name]': '1',
                        'fields[address]': '1',
                        'fields[addresses]': '1',
                        'fields[imageUrl]': '1',
                        'fields[isVerified]': '1',
                        'fields[slug]': '1',
                        'fields[stats.floor_price]': '1',
                        'fields[stats.items_listed]': '1',
                        'fields[stats.num_owners]': '1',
                        'fields[stats.total_supply]': '1',
                        'fields[stats.one_day_change]': '1',
                        'fields[stats.one_day_difference]': '1',
                        'fields[stats.one_day_sales]': '1',
                        'fields[stats.one_day_sales_change]': '1',
                        'fields[stats.one_day_volume]': '1',
                        'fields[stats.rolling_one_day_change]': '1',
                        'fields[stats.rolling_one_day_sales]': '1',
                        'fields[stats.rolling_one_day_sales_change]': '1',
                        'fields[stats.rolling_one_day_volume]': '1',
                        'fields[stats.top_offer_price]': '1',
                        'fields[stats.floor_price_token_price]': '1',
                        'fields[stats.floor_price_token_address]': '1',
                        'fields[stats.floor_price_token_decimals]': '1',
                        'fields[stats.floor_price_token_symbol]': '1',
                        'fields[chainName]': '1',
                        'fields[stats.floor_price_1d]': '1',
                        'sort[stats.rolling_one_day_volume]': '-1',
                        'filters[chainNames][]': 'ethereum',
                        'filters[trending.top_one_day]': 'true',
                        'filters[floorPrice][min]': str(min_price),
                        'filters[floorPrice][max]': str(max_price),
                    }
                )

                offset += 50

                result["items_fetched"] += 50
                for i in response["data"]:
                    result['data'].append(i)

            except Exception as error:
                logger.error(f'Failed to fetch page! limit: {limit} | offset: {offset} | {error}')
                await asyncio.sleep(5)

        return result

    async def fetch_collections(
            self,
            min_price: float,
            max_price: float,
            min_one_day_sellings: int,
            min_one_day_volume: float,
            offer_difference_percent: float
    ) -> list:
        fetch_data = await self.fetch_pages(
            min_price=min_price,
            max_price=max_price
        )

        result = []

        for item in fetch_data["data"]:
            try:
                _item = item["stats"]

                if min_price < _item["floor_price"] < max_price and _item["floor_price_1d"]["change"] < 0.8:
                    if min_one_day_sellings < _item["one_day_sales"]:
                        if min_one_day_volume < _item["one_day_volume"]:
                            percentage_difference = ((_item["floor_price"] - _item["top_offer_price"]) / _item[
                                "floor_price"]) * 100
                            if offer_difference_percent < percentage_difference:
                                result.append(item["slug"])
            except Exception as error:
                logger.error(error)

        return result


async def collections_update_handler() -> None:
    while (await get_data_from_db()):
        try:
            settings = await get_settings_data_from_db()
            parse_settings = settings["collections_parser"]

            client = OpenseaProParser(["http://" + proxy for proxy in settings["proxies"]["main"]])
            collections = await client.fetch_collections(
                min_price=parse_settings["min_price"],
                max_price=parse_settings["max_price"],
                min_one_day_sellings=parse_settings["min_one_day_sellings"],
                min_one_day_volume=parse_settings["min_one_day_volume"],
                offer_difference_percent=parse_settings["offer_difference_percent"]
            )

            await price_requests.submit_items(*collections)
            await update_settings_database({"collections": collections})

            logger.success(f'Updated collections list! New len: {len(collections)}')
            await asyncio.sleep(60)

        except Exception as error:
            print(traceback.format_exc())
            logger.error(f'collections_update_handler: {error}')


####################### REAL PRICES PARSER #######################


class SalesParser(RequestsClient):
    def __init__(self, proxy: list = []) -> None:
        super().__init__(proxy=["http://" + i for i in proxy])

    async def safe_executor(self, function, *args, **kwargs):
        try:
            return await function(*args, **kwargs)
        except Exception as error:
            logger.error(f'Error while processing safe executor: {error}')
            from traceback import format_exc
            print(format_exc())

    @staticmethod
    async def calculate_fair_market_price(prices: list) -> float:
        if len(prices) == 0:
            return 0
        prices = np.array(prices)

        Q1 = np.percentile(prices, 25)
        Q3 = np.percentile(prices, 75)

        IQR = Q3 - Q1

        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR

        filtered_prices = prices[(prices >= lower_bound) & (prices <= upper_bound)]

        return np.median(filtered_prices)

    @staticmethod
    async def calculate_sales_ratio(sales_data: list):
        eth_sales_total = 0
        other_asset_sales = 0

        for sale in sales_data:
            base_asset = sale["baseAsset"]

            if base_asset == "0x0000000000000000000000000000000000000000":
                eth_sales_total += 1
            else:
                other_asset_sales += 1

        return eth_sales_total / ((eth_sales_total + other_asset_sales) / 100 + 1e-6)

    async def fetch_details(self, slug: str) -> dict:
        response = (await self.request(
            "get",
            "https://api.pro.opensea.io/collections/" + slug,
            params=PARAMS
        ))["data"]

        items_response = (
            await self.request(
                "get",
                "https://api.pro.opensea.io/collections/" + slug + "/assets",
                params=FETCH_FLOOR_PRICE
            )
        )["data"]

        floor_price = min(items_response, key=lambda x: x["currentEthPrice"])["currentEthPrice"]
        # logger.debug(f'Floor price for: {slug}: {floor_price / 10**18}')

        return {
            "address": response["addresses"][0]["address"],
            "fees": response["fees"]["openSea"],
            "week_volume": response["sevenDayVolume"],
            "floor": floor_price / 10 ** 18,
            "owned_delta": response["stats"]["total_supply"] / response["stats"]["num_owners"]
        }

    async def fetch_item(self, slug: str, duration: str) -> list:
        """
        durations: 24_hours, 7_days, 30_days, 1_hour, 5_mins
        """

        response = await self.request(
            "get",
            f"https://api.pro.opensea.io/collections%2F{slug}%2Fsales",
            params={"duration": duration}
        )

        price = (await self.calculate_fair_market_price([data["ethPrice"] for data in response["data"]])) / 10 ** 18
        details_data = await self.safe_executor(self.fetch_details, slug)
        sales_ratio_percent = await self.calculate_sales_ratio(response["data"])

        if details_data:
            if details_data["floor"] < price:
                price = details_data["floor"]

        return {
            "item": slug,
            "price": round(price, 5), # is main price
            "details": details_data,
            "sales_ratio_percent": sales_ratio_percent
        }

    async def fetch_collections(self, slugs: list, duration: str) -> list:
        tasks = [
            self.safe_executor(
                self.fetch_item, slug, duration
            ) for slug in slugs
        ]

        fetch_responses = await asyncio.gather(*tasks)

        for response in fetch_responses:
            if response:
                if response["details"]:
                    await add_or_update_item(response)

        return fetch_responses


async def collections_prices_handler() -> None:
    while (await get_data_from_db()):
        try:
            settings = await get_settings_data_from_db()
            parse_settings = settings["collections"]

            client = SalesParser(settings["proxies"]["main"])

            response = await client.fetch_collections(
                parse_settings,
                "24_hours"
            )

            """
            json.dump(
                response, open("resp.json", "w"), indent=2
            )
            """

            logger.success(f'[collections_prices_handler] items in db was updated. Items: {len(response)} :>')

            await asyncio.sleep(60)

        except Exception as error:
            print(traceback.format_exc())
            logger.error(f'collections_update_handler: {error}')
