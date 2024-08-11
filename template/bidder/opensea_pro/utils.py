from web3 import Web3
import random
import time 

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
            "startTime": int(time.time()),
            "endTime": int(time.time() + 60*60*24*15),
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
):
    typed_offer["message"]["zoneHash"] = "0x" + typed_offer["message"]["zoneHash"].hex()
    typed_offer["message"]["conduitKey"] = "0x" + typed_offer["message"]["conduitKey"].hex()

    typed_offer["message"]["offerer"] = Web3.to_checksum_address(typed_offer["message"]["offerer"])
    typed_offer["message"]["zone"] = Web3.to_checksum_address(typed_offer["message"]["zone"])

    typed_offer["message"]["offer"][0]["startAmount"] = str(typed_offer["message"]["offer"][0]["startAmount"])
    typed_offer["message"]["offer"][0]["endAmount"] = str(typed_offer["message"]["offer"][0]["endAmount"])
    typed_offer["message"]["consideration"][0]["startAmount"] = str(typed_offer["message"]["consideration"][0]["startAmount"])
    typed_offer["message"]["consideration"][0]["endAmount"] = str(typed_offer["message"]["consideration"][0]["endAmount"])
    typed_offer["message"]["consideration"][1]["startAmount"] = str(typed_offer["message"]["consideration"][1]["startAmount"])
    typed_offer["message"]["consideration"][1]["endAmount"] = str(typed_offer["message"]["consideration"][1]["endAmount"])

    typed_offer["message"]["consideration"][0]["recipient"] = Web3.to_checksum_address(typed_offer["message"]["consideration"][0]["recipient"])

    typed_offer["message"]["startTime"] = str(typed_offer["message"]["startTime"])
    typed_offer["message"]["endTime"] = str(typed_offer["message"]["endTime"])
    typed_offer["message"]["salt"] = str(typed_offer["message"]["salt"])
    typed_offer["message"]["counter"] = str(typed_offer["message"]["counter"])

    typed_offer["message"]["offer"][0]["identifierOrCriteria"] = str(typed_offer["message"]["offer"][0]["identifierOrCriteria"])

    return {
            'parameters': typed_offer["message"],
            'protocol_address': '0x0000000000000068F116a894984e2DB1123eB395',
            'signature': signature,
            'chainName': 'ethereum',
        }