import tls_client


session = tls_client.Session(

    client_identifier="chrome112",

    random_tls_extension_order=True

)
params={
                        'offset': str(0),
                        'limit': str(50),
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
                        'filters[floorPrice][min]': str(0),
                        'filters[floorPrice][max]': str(1),
                    }

response = session.get(
    "https://api.pro.opensea.io/collections", params=params
)
import json
print(json.dumps(response.headers, indent=2))
<<<<<<< HEAD
=======

>>>>>>> 69cb367df8b1c56129c7f59fa9f055647a33bbef
print(response.status_code)