import os
from typing import Any

import loguru
from aiohttp import web

from aiohttp.web_request import Request

routes = web.RouteTableDef()


@routes.get('/scanner/start')
async def start_get(request: Request):
    uid = request.app['uid']

    if os.path.getsize(f'proxies.txt') == 0:
        loguru.logger.error(f'UNIT:START: proxies.txt is empty')
        return web.Response(status=503, text=f'No proxies provided')

    # todo: run scanner
    # await change_work_statement({"work_statement": True})  # True - софт пашет | False - останавливается
    loguru.logger.info(f'SCANNER:START: scanner {uid} started')

    return web.Response(text='Unit started')


@routes.get('/scanner/get_settings')
async def get_settings_get(request: Request):
    uid = request.app['uid']

    # todo: get settings
    # settings = await get_settings_data_from_db()
    # settings = {
    #     'profit': settings['profit'],
    #     **settings['collections_parser']
    # }
    # loguru.logger.info(f'UNIT:GET_SETTINGS: unit {uid} getting settings')
    # return web.json_response(settings)


def validate_settings(data: dict[str, Any]) -> str | None:
    '''
    :returns str with first invalid parameter or None if all is good
    '''
    # all values are numeric
    for k, v in data.items():
        try:
            a = float(v)
        except ValueError:
            return k

    # all needed fields are presented
    fields = ['min_price', 'max_price', 'min_one_day_sellings', 'min_one_day_volume', 'offer_difference_percent',
              'profit']
    for f in fields:
        if f not in data:
            return f


@routes.post('/scanner/set_settings')
async def set_settings_post(request: web.Request):
    uid = request.app['uid']
    settings = await request.post()

    # todo: set settings
    # try:
    #     if parameter := validate_settings(settings):
    #         return web.Response(status=409, text=f'Неправильно задан параметр {parameter}')
    #
    #     await update_settings_database(
    #         {
    #             "collections_parser": {
    #                 "min_price": settings['min_price'],
    #                 "max_price": settings['max_price'],
    #                 "min_one_day_sellings": settings['min_one_day_sellings'],
    #                 "min_one_day_volume": settings['min_one_day_volume'],
    #                 "offer_difference_percent": settings['offer_difference_percent'],
    #             },
    #             "profit": settings['profit'],
    #         }
    #     )
    #     await set_proxies()
    #
    # except Exception as e:
    #     loguru.logger.error(f'UNIT:SET_SETTINGS: {uid} {str(e)}')
    #     return web.Response(status=500, text=str(e))
    # loguru.logger.info(f'UNIT:SET_SETTINGS: {uid} settings updated successfully')
    # return web.Response(text='Settings updated')
