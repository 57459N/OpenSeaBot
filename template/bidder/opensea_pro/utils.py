from web3 import Web3
import random
from time import time

OPENSEA_PRO_URL = "https://api.pro.opensea.io/"




class ReadyRequest:
    def __init__(self, url: str, method: str, headers: dict = {}, json : dict = {}, proxy: str = None, params: dict = {}) -> None:
        self.url = url
        self.json = json
        self.method = method
        self.headers = headers
        self.proxy = proxy
        self.params = params

    
    async def get_kwargs(self) -> dict:
        return {
            "json": self.json,
            "headers": self.headers,
            "proxy": self.proxy,
            "params": self.params
        }
    

async def get_seaport_typed_data(
        address: str,
        nft_address: str,
        zone: str,
        zone_hash: str,
        price: int,
        start_time: int,
        end_time: int,
        salt: str,
        conduit_key: str,
        order_type: int,
        comission: int
):
    return {
        "types": {
            "EIP712Domain": [
                {
                    "name": "name",
                    "type": "string"
                },
                {
                    "name": "version",
                    "type": "string"
                },
                {
                    "name": "chainId",
                    "type": "uint256"
                },
                {
                    "name": "verifyingContract",
                    "type": "address"
                }
            ],
            "OrderComponents": [
                {
                    "name": "offerer",
                    "type": "address"
                },
                {
                    "name": "zone",
                    "type": "address"
                },
                {
                    "name": "offer",
                    "type": "OfferItem[]"
                },
                {
                    "name": "consideration",
                    "type": "ConsiderationItem[]"
                },
                {
                    "name": "orderType",
                    "type": "uint8"
                },
                {
                    "name": "startTime",
                    "type": "uint256"
                },
                {
                    "name": "endTime",
                    "type": "uint256"
                },
                {
                    "name": "zoneHash",
                    "type": "bytes32"
                },
                {
                    "name": "salt",
                    "type": "uint256"
                },
                {
                    "name": "conduitKey",
                    "type": "bytes32"
                },
                {
                    "name": "counter",
                    "type": "uint256"
                }
            ],
            "OfferItem": [
                {
                    "name": "itemType",
                    "type": "uint8"
                },
                {
                    "name": "token",
                    "type": "address"
                },
                {
                    "name": "identifierOrCriteria",
                    "type": "uint256"
                },
                {
                    "name": "startAmount",
                    "type": "uint256"
                },
                {
                    "name": "endAmount",
                    "type": "uint256"
                }
            ],
            "ConsiderationItem": [
                {
                    "name": "itemType",
                    "type": "uint8"
                },
                {
                    "name": "token",
                    "type": "address"
                },
                {
                    "name": "identifierOrCriteria",
                    "type": "uint256"
                },
                {
                    "name": "startAmount",
                    "type": "uint256"
                },
                {
                    "name": "endAmount",
                    "type": "uint256"
                },
                {
                    "name": "recipient",
                    "type": "address"
                }
            ]
        },
        "primaryType": "OrderComponents",
        "domain": {
            "name": "Seaport",
            "version": "1.6",
            "chainId": 1,
            "verifyingContract": "0x0000000000000068f116a894984e2db1123eb395"
        },
        "message": {
            "offerer": address.lower(),
            "offer": [
                {
                    "itemType": 1,
                    "token": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
                    "identifierOrCriteria": 0,
                    "startAmount": int(price),
                    "endAmount": int(price)
                }
            ],
            "zone": zone,
            "zoneHash": bytes.fromhex(zone_hash[2:]),
            "consideration": [
                {
                    "itemType": 4,
                    "token": nft_address.lower(),
                    "identifierOrCriteria": 0,
                    "startAmount": 1,
                    "endAmount": 1,
                    "recipient": address.lower()
                },
                {
                    "itemType": 1,
                    "token": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
                    "identifierOrCriteria": 0,
                    "startAmount": int(comission),
                    "endAmount": int(comission),
                    "recipient": "0x0000a26b00c1f0df003000390027140000faa719"
                }
            ],
            "startTime": int(start_time),
            "endTime": int(end_time),
            "orderType": int(order_type),
            "salt": int(salt),
            "conduitKey": bytes.fromhex(conduit_key[2:]),
            "totalOriginalConsiderationItems": 2,
            "counter": 0
        }
    }


async def get_seaport_offer_data_json(
        typed_offer: dict,
        slug: str,
        signature: str
):
    typed_offer["message"]["zoneHash"] = "0x" + typed_offer["message"]["zoneHash"].hex()
    typed_offer["message"]["conduitKey"] = "0x" + typed_offer["message"]["conduitKey"].hex()

    typed_offer["message"]["offerer"] = Web3.to_checksum_address(typed_offer["message"]["offerer"])
    typed_offer["message"]["zone"] = Web3.to_checksum_address(typed_offer["message"]["zone"])

    typed_offer["message"]["offer"][0]["startAmount"] = str(typed_offer["message"]["offer"][0]["startAmount"])
    typed_offer["message"]["offer"][0]["endAmount"] = str(typed_offer["message"]["offer"][0]["endAmount"])
    typed_offer["message"]["consideration"][0]["identifierOrCriteria"] = str(typed_offer["message"]["consideration"][0]["identifierOrCriteria"])
    typed_offer["message"]["consideration"][0]["startAmount"] = str(typed_offer["message"]["consideration"][0]["startAmount"])
    typed_offer["message"]["consideration"][0]["endAmount"] = str(typed_offer["message"]["consideration"][0]["endAmount"])
    typed_offer["message"]["consideration"][1]["startAmount"] = str(typed_offer["message"]["consideration"][1]["startAmount"])
    typed_offer["message"]["consideration"][1]["endAmount"] = str(typed_offer["message"]["consideration"][1]["endAmount"])

    typed_offer["message"]["consideration"][0]["recipient"] = Web3.to_checksum_address(typed_offer["message"]["consideration"][0]["recipient"])

    typed_offer["message"]["startTime"] = str(typed_offer["message"]["startTime"])
    typed_offer["message"]["salt"] = str(typed_offer["message"]["salt"])
    typed_offer["message"]["counter"] = str(typed_offer["message"]["counter"])

    return {
        'criteria': {
            'collection': {
                'slug': slug,
            },
        },
        'protocol_data': {
            'parameters': typed_offer["message"],
            'signature': signature,
        },
        'protocol_address': '0x0000000000000068F116a894984e2DB1123eB395',
        'chainName': 'ethereum',
    }




async def get_random_int(size: int) -> int:
    return int(''.join(str(random.randint(1, 9)) for _ in range(size)))

async def round_to_multiple(number: int, multiple: int = 100000000000000):
    return round(number / multiple) * multiple

async def generate_selling_data(
        offerer: str,
        token_address: str,
        item_ids: list,
        price: int,
        comission: float = 0.5

):
    comission_amount = int((price / 100) * comission)
    price_with_commission = price - comission_amount

    return {
            "offerer": offerer.lower(),
            "offer": [
                {
                    "itemType": 2,
                    "token": token_address.lower(),
                    "identifierOrCriteria": item_id,
                    "startAmount": 1,
                    "endAmount": 1
                } for item_id in item_ids
            ],
            "consideration": [
                {
                    "itemType": 0,
                    "token": "0x0000000000000000000000000000000000000000",
                    "identifierOrCriteria": 0,
                    "startAmount": (await round_to_multiple(price_with_commission * len(item_ids))),
                    "endAmount": (await round_to_multiple(price_with_commission * len(item_ids))),
                    "recipient": offerer.lower()
                },
                {
                    "itemType": 0,
                    "token": "0x0000000000000000000000000000000000000000",
                    "identifierOrCriteria": 0,
                    "startAmount": int(comission_amount * len(item_ids)),
                    "endAmount": int(comission_amount * len(item_ids)),
                    "recipient": "0x0000a26b00c1f0df003000390027140000faa719"
                }
            ],
            "startTime": int(time()),
            "endTime": int(time() + 60*31),
            "orderType": 0,
            "zone": "0x004c00500000ad104d7dbd00e3ae0a5c00560c00",
            "zoneHash": bytes.fromhex("0000000000000000000000000000000000000000000000000000000000000000"),
            "salt": 51951570786726798460324975021501917861654789585098516727730144917737880043544,
            "conduitKey": bytes.fromhex("0000007b02230091a7ed01230072f7006a004d60a8d4e71d599b8104250f0000"),
            "totalOriginalConsiderationItems": 2,
            "counter": 0
        }

async def build_selling_data(
        offerer: str,
        offer_data: dict
):
    return {
        "types": {
            "EIP712Domain": [
                {
                    "name": "name",
                    "type": "string"
                },
                {
                    "name": "version",
                    "type": "string"
                },
                {
                    "name": "chainId",
                    "type": "uint256"
                },
                {
                    "name": "verifyingContract",
                    "type": "address"
                }
            ],
            "OrderComponents": [
                {
                    "name": "offerer",
                    "type": "address"
                },
                {
                    "name": "zone",
                    "type": "address"
                },
                {
                    "name": "offer",
                    "type": "OfferItem[]"
                },
                {
                    "name": "consideration",
                    "type": "ConsiderationItem[]"
                },
                {
                    "name": "orderType",
                    "type": "uint8"
                },
                {
                    "name": "startTime",
                    "type": "uint256"
                },
                {
                    "name": "endTime",
                    "type": "uint256"
                },
                {
                    "name": "zoneHash",
                    "type": "bytes32"
                },
                {
                    "name": "salt",
                    "type": "uint256"
                },
                {
                    "name": "conduitKey",
                    "type": "bytes32"
                },
                {
                    "name": "counter",
                    "type": "uint256"
                }
            ],
            "OfferItem": [
                {
                    "name": "itemType",
                    "type": "uint8"
                },
                {
                    "name": "token",
                    "type": "address"
                },
                {
                    "name": "identifierOrCriteria",
                    "type": "uint256"
                },
                {
                    "name": "startAmount",
                    "type": "uint256"
                },
                {
                    "name": "endAmount",
                    "type": "uint256"
                }
            ],
            "ConsiderationItem": [
                {
                    "name": "itemType",
                    "type": "uint8"
                },
                {
                    "name": "token",
                    "type": "address"
                },
                {
                    "name": "identifierOrCriteria",
                    "type": "uint256"
                },
                {
                    "name": "startAmount",
                    "type": "uint256"
                },
                {
                    "name": "endAmount",
                    "type": "uint256"
                },
                {
                    "name": "recipient",
                    "type": "address"
                }
            ]
        },
        "primaryType": "OrderComponents",
        "domain": {
            "name": "Seaport",
            "version": "1.6",
            "chainId": 1,
            "verifyingContract": "0x0000000000000068f116a894984e2db1123eb395"
        },
        "message": await generate_selling_data(
                offerer, 
                offer_data["token_address"], 
                offer_data["identifierOrCriteria"], 
                offer_data["price"], 
                comission=0.5099
            )
        
    }


async def get_seaport_selling_data_json(
    typed_offer: dict,
    signature: str
) -> dict:
    def to_hex(value):
        return f"0x{value.hex()}"

    def to_checksum(value):
        return Web3.to_checksum_address(value)

    def to_str(value):
        return str(value)

    message = typed_offer["message"]

    message["zoneHash"] = to_hex(message["zoneHash"])
    message["conduitKey"] = to_hex(message["conduitKey"])

    message["offerer"] = to_checksum(message["offerer"])
    message["zone"] = to_checksum(message["zone"])

    offer = message["offer"][0]
    consideration = message["consideration"]

    offer["startAmount"] = to_str(offer["startAmount"])
    offer["endAmount"] = to_str(offer["endAmount"])
    offer["identifierOrCriteria"] = to_str(offer["identifierOrCriteria"])

    for consideration_item in consideration:
        consideration_item["startAmount"] = to_str(consideration_item["startAmount"])
        consideration_item["endAmount"] = to_str(consideration_item["endAmount"])
        consideration_item["recipient"] = to_checksum(consideration_item["recipient"])

    message["startTime"] = to_str(message["startTime"])
    message["endTime"] = to_str(message["endTime"])
    message["salt"] = to_str(message["salt"])
    message["counter"] = to_str(message["counter"])

    return {
        'parameters': message,
        'protocol_address': '0x0000000000000068F116a894984e2DB1123eB395',
        'signature': signature,
        'chainName': 'ethereum',
    }

async def fetch_pro_current_prices(profit: float, current_prices: list, my_current_orders: dict):
    change_items = []

    for item in current_prices:
        try:
            slug = item.get("slug")
            my_order_price = float(my_current_orders.get(slug, 0))

            best_bid = item.get("best_bid", {})
            best_bid_price = float(best_bid.get("price", 0) / 10**18)

            orders = item.get("orders", [])
            second_bid_price = float(min(orders, key=lambda x: x.get("price", float('inf'))).get("price", 0) / 10**18)

            floor_price = float(item.get("floor_price", 0) / 10**18)

            if my_order_price < best_bid_price:
                if floor_price * (1 - profit) > best_bid_price + 0.001:
                    change_items.append({
                        "name": slug, 
                        "price": round(best_bid_price + 0.0001, 4), 
                        "address": item.get("address")
                    })
            elif best_bid_price == my_order_price:
                if second_bid_price + 0.001 < my_order_price:
                    if floor_price * (1 - profit) > second_bid_price + 0.001:
                        change_items.append({
                            "name": slug, 
                            "price": round(second_bid_price + 0.0001, 4), 
                            "address": item.get("address")
                        })

        except (TypeError, ValueError) as error:
            print(f'fetch_pro_current_prices: Invalid data for {slug} - {error}')
        except Exception as error:
            print(f'fetch_pro_current_prices: Error processing {slug} - {error}')
    
    return change_items