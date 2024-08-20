from datetime import datetime
from utils.database import get_items_by_names


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

async def fetch_current_prices(profit: float, current_prices: dict, my_current_orders: dict):
    change_items = []

    items_market_data = await get_items_by_names(list(current_prices.keys()))

    for slug, price in current_prices.items():
        slug = slug.replace("_pro", "")
        try:
            my_order_price = float(my_current_orders.get(slug, 0))
            item_market_data = items_market_data[slug]

            if not price: best_bid_price = 0
            else: best_bid_price = price
            
            floor_price = item_market_data.get("price", 0)
            sales_ratio_percent = item_market_data.get("sales_ratio_percent", 0)

            if sales_ratio_percent > 60:
                potential_new_price = round(best_bid_price + 0.0001, 4)
                if my_order_price < best_bid_price and floor_price * (1 - profit) > best_bid_price + 0.001:
                    change_items.append(
                        {
                            "name": slug,
                            "price": potential_new_price,
                            "address": item_market_data["details"].get("address")
                        }
                    )

        except Exception as error:
            pass
        
    return change_items