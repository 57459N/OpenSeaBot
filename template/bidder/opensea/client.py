from requests_client.client import RequestsClient
from eth_account import Account
from bidder.opensea.types.api_types import Queries, Endpoints, PaymentAssets, Offer, Query
from eth_account.messages import encode_defunct, encode_structured_data
from time import time
import json
from bidder.opensea.utils import *
from random import choice
import asyncio
from loguru import logger

from traceback import format_exc
from utils.database import get_item_by_name


class OpenseaAccount(RequestsClient):
    def __init__(self, secret_key: str, proxy: list = []) -> None:
        super().__init__(proxy=["http://" + i for i in proxy])

        self.account: Account = Account.from_key(secret_key)
        self.address: str = self.account.address
        self.session_cookies = {}

    async def safe_executor(self, function, *args, **kwargs):
        try:
            return await function(*args, **kwargs)
        except Exception as error:
            logger.error(f'Error while processing safe executor: {error}')
            print(format_exc())

    async def sign_message(self, message, _type: str = "stringMessage") -> str:
        if _type == "stringMessage":
            message = encode_defunct(text=message)
        elif _type == "TYPED_DATA_V4":
            message = encode_structured_data(message)

        return self.account.sign_message(message).signature.hex()

    async def _get_login_signature_message(self) -> str:
        response = await self.send_request(Queries.get_login_message, {'address': self.address.lower()})
        return response["data"]["auth"]["loginMessage"]

    async def _get_create_offer_signature_message(self, offer: Offer, closed_time: int) -> dict:
        timestamp = await get_format_timestamp(int(time() + closed_time))

        variables = {
            'price': {
                'paymentAsset': PaymentAssets.weth,
                'amount': offer.price,
            },
            'closedAt': timestamp,
            'assetContract': {
                'contractAddress': offer.colection_address.lower(),
                'chain': 'ETHEREUM',
            },
            'collection': offer.collection_name,
            'trait': None,
            'quantity': '1',
        }

        response = await self.send_request(Queries.create_collection, variables)
        if len(response["data"]["blockchain"]["createCollectionOfferActions"]) == 1:
            return response["data"]["blockchain"]["createCollectionOfferActions"][0]["method"]
        else:
            raise Exception(f"[{self.address}] must approve weth from spending on Opensea")

    async def login(self) -> None:
        message_text = await self._get_login_signature_message()
        signature: str = await self.sign_message(message=message_text)

        variables = {
            'address': self.address.lower(),
            'message': message_text,
            'deviceId': '28e4b8e1-74b8-458b-870d-b8d81e5a0aa8',
            'signature': signature,
            'chain': 'ETHEREUM',
        }

        response = await self.send_request(Queries.auth_login, variables)
        if "data" in response.keys():
            self.session_cookies.update(await self.get_cookies())
            self.cookies = self.session.cookie_jar
            return True
        else:
            raise Exception(f"Failed login to OpenSea, response: {response}")

    async def create_collection_offer(self, offer: Offer, closed_time: int = 60000,
                                      fetched_response: bool = False) -> dict:
        create_data = await self._get_create_offer_signature_message(offer, closed_time)
        await asyncio.sleep(0.5)

        server_signature = create_data["serverSignature"]
        client_message = await get_format_typed_message(
            json.loads(create_data["clientMessage"])
        )
        sign_data = create_data["orderData"]
        sign_type = create_data["clientSignatureStandard"]
        signature = await self.sign_message(client_message, _type=sign_type)

        variables = {
            'orderData': sign_data,
            'clientSignature': signature,
            'serverSignature': server_signature,
        }

        response = await self.send_request(Queries.create_order, variables)
        if fetched_response:
            return {"create_order": response}

        return response

    async def get_listings(self, return_list: list = [], collections: list = []) -> list:
        # await self.close_session()

        variables = {
            'filterByOrderRules': True,
            'isExpired': False,
            'makerAssetIsPayment': True,
            'collections': collections if len(collections) != 0 else None,
            'identity': {
                'address': self.address,
            },
            'sortAscending': None,
            'includeInvalidBids': False,
            'sortBy': 'OPENED_AT',
            'maker': {
                'address': self.address,
            },
            'orderStatusToggles': [
                'ACTIVE',
            ],
            'offerTypeToggles': [
                'COLLECTION',
            ],
            'includeCriteriaOrders': True,
            'cursor': None,
            'count': 32
        }

        response = await self.send_request(Queries.get_all_listings, variables)
        orders_info = response["data"]["orders"]["edges"]

        if len(collections) == 0:
            return orders_info

        for order in orders_info:
            if order["node"]["criteria"]["collection"]["slug"] in collections and order["node"]["isValid"] and \
                    order["node"]["item"]["isDelisted"] is False:
                return_list.append(order)

        return return_list

    async def close_all_active_offers(self, offers: list = [1, 2, 3]) -> dict:
        while len(offers) != 0:
            offers = await self.get_listings()
            orders = [offer["node"]["id"] for offer in offers]

            response = await self.send_request(Queries.cancel_orders, {'orders': orders})
            return response

    async def close_collection_worst_orders(self, close_data: dict) -> dict:
        """
        close_data = {
            "name1": price,
            "name2": price,
            "name3": price
        }
        """
        logger.debug(f'Close data: {close_data}')
        response = await self.get_listings(collections=[])  # collections=list(close_data.keys())

        bad_orders = []
        for item in response:
            slug = item["node"]["item"]["collection"]["slug"]
            if slug in close_data.keys():
                if float(item["node"]["priceType"]["unit"]) != close_data[slug]:
                    bad_orders.append(item["node"]["relayId"])
                    # print(json.dumps(item, indent=2))

        if len(bad_orders) == 0:
            return {}

        # logger.debug(f'Bad orders: {bad_orders}')

        response = await self.send_request(Queries.cancel_orders, {'orders': bad_orders}, without_response=True)
        # logger.debug(f'Cancel response: {response}')
        return response

    async def get_collection_best_offer(self, collection_slug: str) -> float:
        variables = {
            'collection': collection_slug
        }
        response = await self.send_request(Queries.collegtion_best_offer, variables)
        try:

            if len(response["data"]["collection"]["collectionOffers"]["edges"]) == 0:
                min_bid = 9999999999999999999
            else:
                min_bid = float(
                    response["data"]["collection"]["collectionOffers"]["edges"][0]["node"]["perUnitPriceType"]["unit"]
                )
        except:
            logger.error(f'Session is dead, will make relogin')
            await self.login()
            return await self.get_collection_best_offer(collection_slug)

        database_data = await get_item_by_name(collection_slug)

        return {
            "min_bid": min_bid,
            "floor_price": database_data["price"],
            "slug": collection_slug,
            "address": database_data["details"]["address"],
            "sales_ratio_percent": database_data["sales_ratio_percent"]
        }

    async def get_collection_offers(self, contract_address: str) -> float:
        variables = {
            'cursor': None,
            'count': 2,
            'excludeMaker': None,
            'isExpired': False,
            'isValid': True,
            'includeInvalidBids': None,
            'isInactive': None,
            'maker': None,
            'makerArchetype': None,
            'makerAssetIsPayment': True,
            'takerArchetype': {
                'assetContractAddress': contract_address,
                'tokenId': '764',
                'chain': 'ETHEREUM',
            },
            'takerAssetCollections': None,
            'takerAssetIsOwnedBy': None,
            'takerAssetIsPayment': None,
            'sortAscending': None,
            'sortBy': 'PRICE',
            'makerAssetBundle': None,
            'takerAssetBundle': None,
            'expandedMode': False,
            'isBid': True,
            'filterByOrderRules': True,
            'includeCriteriaOrders': True,
            'criteriaTakerAssetId': 'QXNzZXRUeXBlOjE2MjgyNDM0NTI=',
            'includeCriteriaTakerAsset': True,
            'isSingleAsset': True,
        }
        response = await self.send_request(Queries.collegtion_page, variables)
        # checker on valid response

        return {
            "contract": response["data"]["orders"]["edges"][0]["node"]["item"]["assetContract"]["address"],
            "orders": [
                {
                    "price": float(item["node"]["perUnitPriceType"]["eth"]),
                    "maker": item["node"]["maker"]["address"]
                }
                for item in response["data"]["orders"]["edges"] if item["node"]["side"] == "BID"
            ],
            "floor": float(
                response["data"]["orders"]["edges"][0]["node"]["item"]["collection"]["statsV2"]["floorPrice"]["eth"]),
        }

    async def change_settings(self, username: str, bio: str, email: str = "", website_url: str = "") -> dict:
        variables = {
            "input": {
                'bio': bio,
                'email': email,
                'username': username,
                'websiteUrl': website_url,
            }
        }
        return await self.send_request(Queries.change_settings, variables)

    async def get_all_orders(self) -> None:
        pass

    async def send_request(self, query: Query, variables: dict, without_response: bool = False) -> dict:
        kwargs = {
            "json": {
                'id': query.id,
                'query': query.text,
                "variables": variables
            },
            "headers": {
                'x-signed-query': query.signed,
                "x-auth-address": self.address.lower(),
                'x-kl-saas-ajax-request': 'Ajax_Request',
                'x-app-id': 'opensea-web'
            }
        }
        if without_response:
            response = await self.request_without_response("post", Endpoints.api_graphql, **kwargs)
        else:
            response = await self.request("post", Endpoints.api_graphql, **kwargs)
        return response
