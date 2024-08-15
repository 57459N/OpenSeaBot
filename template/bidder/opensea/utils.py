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

async def fetch_current_prices(profit: float, current_prices: list, my_current_orders: dict):
    change_items = []

    for item in current_prices:
        try:
            slug = item.get("slug")
            my_order_price = float(my_current_orders.get(slug, 0))
            best_bid_price = item.get("min_bid", 0)
            floor_price = item.get("floor_price", 0)
            sales_ratio_percent = item.get("sales_ratio_percent", 0)

            if sales_ratio_percent > 60:
                potential_new_price = round(best_bid_price + 0.0001, 4)
                if my_order_price < best_bid_price and floor_price * (1 - profit) > best_bid_price + 0.001:
                    change_items.append(
                        {
                            "name": slug,
                            "price": potential_new_price,
                            "address": item.get("address")
                        }
                    )

        except (TypeError, ValueError) as error:
            print(f'fetch_current_prices. Invalid data: {item} - {error}')
        except Exception as error:
            print(f'fetch_current_prices: {item} - {error}')
        
    return change_items