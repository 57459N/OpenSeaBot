from requests_client.client import RequestsClient
from eth_account import Account
from eth_account.messages import encode_defunct, encode_structured_data
from time import time
import json
from bidder.opensea_pro.utils import *
from random import choice
import asyncio
from traceback import format_exc
from loguru import logger
from utils.database import get_item_by_name

ABI = [
    {
        "inputs": [
        {
            "internalType": "address",
            "name": "owner",
            "type": "address"
        },
        {
            "internalType": "address",
            "name": "operator",
            "type": "address"
        }
        ],
        "name": "isApprovedForAll",
        "outputs": [
        {
            "internalType": "bool",
            "name": "",
            "type": "bool"
        }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
        {
            "internalType": "address",
            "name": "operator",
            "type": "address"
        },
        {
            "internalType": "bool",
            "name": "approved",
            "type": "bool"
        }
        ],
        "name": "setApprovalForAll",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
  },
  {
        "inputs": [
        {
            "internalType": "address",
            "name": "owner",
            "type": "address"
        },
        {
            "internalType": "address",
            "name": "operator",
            "type": "address"
        }
        ],
        "name": "allowance",
        "outputs": [
            {
            "internalType": "uint256",
            "name": "operator",
            "type": "uint256"
        }
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

class OpenseaProAccount(RequestsClient):
    def __init__(self, secret_key: str, proxy: list = []) -> None:
        super().__init__(proxy=["http://" + i for i in proxy])

        self.account: Account = Account.from_key(secret_key)
        self.address: str = self.account.address
        self.session_cookies = {}

        self.auth_token = ''


    async def sign_message(self, message, _type: str = "stringMessage") -> str:
        if _type == "stringMessage":
            message = encode_defunct(text=message)
        elif _type == "TYPED_DATA_V4":
            message=encode_structured_data(message)
        
        return self.account.sign_message(message).signature.hex()
    
    async def _get_login_signature_message(self) -> str:
        response = await self.request(
            "get", OPENSEA_PRO_URL + "auth%2Fmessage%2F" + self.address
        )

        return response["data"]["message"]
    
    async def fetch_collection(self, slug: str) -> dict:
        response = await self.request(
            "get", OPENSEA_PRO_URL + "collections%2F" + slug + "%2Forderbook%2Fdepth"
        )

        bids = [item for item in response["data"][0]["offers"] if item["orderType"] == "collection_offer" and item["market"] == "seaport"]
        database_data = await get_item_by_name(slug)

        if len(bids) == 0:
            bids = [{"price": 0}]

        return {
            "best_bid": max(bids, key=lambda x: x["price"]),
            "orders": sorted(bids, key=lambda x: x["price"], reverse=True)[:2],
            "slug": slug,
            "floor_price": database_data["price"]
        }
    
    async def get_account_assets(self) -> dict:
        response = await self.send_request(
            ReadyRequest(
                url=f"{OPENSEA_PRO_URL}opensea%2Faccount%2F{self.address}%2Fassets",
                method="get",
                params={
                    'limit': '100',
                    'collectionSlugs': '',
                    'excludePrivateOwnerships': 'true',
                    'excludeDelistedAssets': 'true',
                    'chainName': 'ethereum',
                }
            )
        )
            
        return response
    
    async def seaport_selling(
            self, sell_data: dict
    ) -> dict:
        
        """
            sell_data: 
                {
                    "identifierOrCriteria": [1, 2, 33 ...],
                    "price": 995000000000000000,
                    "token_address": "0x062e691c2054de82f28008a8ccc6d7a1c8ce060d"
                }
            
            """
        
        offer_data = await build_selling_data(self.address, sell_data)
        signature = await self.sign_message(offer_data, _type="TYPED_DATA_V4")
        json_data = await get_seaport_selling_data_json(offer_data, signature)

        response = await self.send_request(
            ReadyRequest(
                url=f"{OPENSEA_PRO_URL}opensea%2Flisting",
                method="post",
                json=json_data
            )
        )
        return response
    
    async def get_account_portfolio(self, resp: dict = {}, simple_resp: bool = False) -> dict:
        response = await self.send_request(
            ReadyRequest(
                url=f"{OPENSEA_PRO_URL}account%2F{self.address}%2Fcollections",
                method="get",
                params={
                    'chainName': 'ethereum',
                    'excludePrivateOwnerships': 'true',
                    'excludeDelistedAssets': 'true',
                    'limit': '100',
                    'sort': 'estimated_value',
                }
            )
        )
        if simple_resp: return response
        
        for item in response["data"]["collections"]:
            resp.update({item["slug"]:item["numItemsOwned"]})
            
        return resp
    
    async def safe_executor(self, function, *args, **kwargs):
        try:
            return await function(*args, **kwargs)
        except Exception as error:
            print(format_exc())
            logger.error(f'Error while processing safe1 executor: {error}')
        


    async def login(self) -> None:
        login_message = await self._get_login_signature_message()

        response = await self.send_request(
            ReadyRequest(
                url=f'{OPENSEA_PRO_URL}auth%2Flogin',
                method="post",
                json={
                    'signature': await self.sign_message(login_message),
                    'signer': self.address,
                    'message': login_message,
                }
            )
        )

        if response["data"] != "Login Successfully":
            raise Exception(str(response))
        
        self.auth_token = response["token"]


    async def close_orders(self, order_list: list) -> dict:
        return await self.send_request(
            ReadyRequest(
                url=OPENSEA_PRO_URL + "opensea%2Foffer%2Fcancel",
                method="post",
                json={
                    'orderHashes': order_list,
                    'exchangeContractAddress': '0x0000000000000068f116a894984e2db1123eb395',
                }
            )
        )
    
    async def get_active_offers(self, slug: str = '') -> list:
        response = await self.send_request(
            ReadyRequest(
                url=f'{OPENSEA_PRO_URL}opensea%2Faccount%2F{self.address}%2Foffers',
                method="post",
                json={
                    'collectionSlug': slug,
                    'fields': {
                        'remaining_quantity': 1,
                        'protocol_address': 1,
                        'created_date': 1,
                        'protocol_data.parameters': 1,
                        'protocol_data.startTime': 1,
                        'protocol_data.endTime': 1,
                        'current_price': 1,
                        'listing_time': 1,
                        'expiration_time': 1,
                        'order_hash': 1,
                        'trait_criteria': 1,
                        'collection_slug': 1,
                        'order_type': 1,
                        'is_awaiting_gasless_cancellation_status': 1,
                    },
                },
                params={
                    'order_by': 'created_date',
                    'limit': '50',
                    'order_direction': 'desc',
                    'state': 'active',
                }
            )
        )

        return [
            {
                "slug": offer["collection_slug"],
                "price": int(offer["current_price"]),
                "hash": offer["order_hash"]
            } for offer in response["offers"]
        ]
    

    async def build_seaport_offer(
            self, 
            comission: float, 
            nft_address: str,
            price: int
    ) -> dict:
        """
        response = await self.send_request(
            ReadyRequest(
                url=f"{OPENSEA_PRO_URL}opensea%2FbuildSeaportOffer",
                method="post",
                json={
                    'offerer': self.address,
                    'quantity': 1,
                    'protocol_address': '0x0000000000000068F116a894984e2DB1123eB395',
                    'criteria': {
                        'collection': {
                            'slug': slug,
                        },
                    },
                }
            )
        )
        """

        response = {
            "partialParameters": {
                "consideration": [
                    {
                        "itemType": 4,
                        "token": "0xbd3531da5cf5857e7cfaa92426877b022e612cf8",
                        "identifierOrCriteria": "0",
                        "startAmount": "1",
                        "endAmount": "1",
                        "recipient": "0x37fB0A005AC9FAdB77f14710da04DF6970A5ecc8"
                    }
                ],
                "zone": "0x000056f7000000ece9003ca63978907a00ffd100",
                "zoneHash": "0x0000000000000000000000000000000000000000000000000000000000000000"
            }
        }
        now_time = int(time())
        comission_price = int((price / 100) * comission)

        return await get_seaport_typed_data(
            address=self.address,
            nft_address=nft_address,
            zone=response["partialParameters"]["zone"],
            zone_hash=response["partialParameters"]["zoneHash"],
            price=price,
            start_time=now_time,
            end_time=now_time + 60*52,
            salt="519515707867267984603249750215019178616547895850985167277303" + str(await get_random_int(17)),
            conduit_key="0x0000007b02230091a7ed01230072f7006a004d60a8d4e71d599b8104250f0000",
            order_type=2,
            comission=comission_price
        )
    
    async def seaport_offer(
        self, 
        slug: str, 
        comission: float, 
        nft_address: str, 
        price: int
    ):
        price = await round_to_multiple(price)

        offer_data = await self.build_seaport_offer(comission, nft_address, price)
        signature = await self.sign_message(offer_data, _type="TYPED_DATA_V4")
        request_data = await get_seaport_offer_data_json(offer_data, slug, signature)

        response = await self.send_request(
            ReadyRequest(
                url=f"{OPENSEA_PRO_URL}opensea%2FseaportOffer",
                method="post",
                json=request_data
            ),
            without_response=True
        )
        return response

    
    async def send_request(self, request: ReadyRequest, without_response: bool = False) -> dict:
        if len(self.auth_token) > 10:
            request.headers["token"] = self.auth_token
        
        if without_response:
            response = await self.request_without_response(
                request.method,
                request.url,
                **(await request.get_kwargs())
            )
        else:
            response = await self.request(
                request.method,
                request.url,
                **(await request.get_kwargs())
            )
            
        return response