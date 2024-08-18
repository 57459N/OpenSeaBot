import loguru
from aiohttp import web
from aiohttp.web_request import Request
from server.price_parser import parser as price_parser

routes = web.RouteTableDef()


@routes.post('/price_parser/add_collections')
async def add_collections_handler(request: Request):
    try:
        collections = await request.json()
        if not isinstance(collections, list):
            raise ValueError
        for el in collections:
            if not isinstance(el, str):
                raise ValueError
    except ValueError:
        loguru.logger.warning(f'PRICE_PARSER:ADD_COLLECTIONS: bad request')
        return web.Response(status=400, text='`collections` must be a list of strings in json format')

    try:
        await price_parser.submit_items(*collections)
        return web.Response()
    except Exception as e:
        loguru.logger.error(f'PRICE_PARSER:ADD_COLLECTIONS: {e}')
        return web.Response(status=500, text=str(e))


@routes.post('/price_parser/get_prices')
async def get_prices_handler(request: Request):
    try:
        collections = await request.json()
        if not isinstance(collections, list):
            raise ValueError
        for el in collections:
            if not isinstance(el, str):
                raise ValueError
    except ValueError:
        loguru.logger.warning(f'PRICE_PARSER:ADD_COLLECTIONS: bad request')
        return web.Response(status=400, text='`collections` must be a list of strings in json format')

    prices = {slug: price_parser.get_item_value(slug) for slug in collections}
    return web.json_response(prices)
