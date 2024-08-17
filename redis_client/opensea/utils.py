from datetime import datetime


async def get_format_timestamp(_time: int) -> str:
    return datetime.utcfromtimestamp(_time).isoformat() + 'Z'


async def get_format_typed_message(client_message: dict) -> dict:
    client_message["domain"]["chainId"] = 1

    for name in ["orderType", "startTime", "endTime", "salt", "counter"]:
        client_message["message"][name] = int(client_message["message"][name])

    for name in ["zoneHash", "conduitKey"]:
        client_message["message"][name] = bytes.fromhex(client_message["message"][name][2:])

    for name in client_message["message"].keys():
        if type(client_message["message"][name]) is list:
            for _data in client_message["message"][name]:
                for value in _data.keys():
                    try:
                        _data[value] = int(_data[value])
                    except: pass
        
    return client_message