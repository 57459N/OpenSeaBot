import os
from typing import Any

import loguru
from aiohttp import web

from utils.unit import start_program
from utils.database import get_data_from_db, change_work_statement, get_settings_data_from_db, update_settings_database
from aiohttp.web_request import Request

from utils.unit import set_proxies

routes = web.RouteTableDef()


@routes.get('/unit/start')
async def start_get(request: Request):
    uid = request.app['uid']
    is_running = await get_data_from_db()
    if is_running:
        loguru.logger.warning(f'UNIT:START: unit {uid} is already running')
        return web.Response(status=200, text=f'Unit is already running')

    if os.path.getsize(f'proxies.txt') == 0:
        loguru.logger.error(f'UNIT:START: proxies.txt is empty')
        return web.Response(status=503, text=f'No proxies provided')

    await change_work_statement({"work_statement": True})  # True - софт пашет | False - останавливается
    await start_program()
    loguru.logger.info(f'UNIT:START: unit {uid} started')

    return web.Response(text='Unit started')


@routes.get('/unit/is_running')
async def is_running_get(request: Request):
    is_running = await get_data_from_db()
    uid = request.app['uid']
    if is_running:
        loguru.logger.info(f'UNIT:IS_RUNNING: unit {uid} is running')
        return web.Response(text='True')
    else:
        loguru.logger.info(f'UNIT:IS_RUNNING: unit {uid} is not running')
        return web.Response(text='False')


@routes.get('/unit/stop')
async def stop_get(request):
    loguru.logger.info('STOP')
    uid = request.app['uid']
    is_running = await get_data_from_db()
    if not is_running:
        loguru.logger.warning(f'UNIT:STOP: unit {uid} is already stopped')
        return web.Response(status=409, text=f'Unit {uid} is already stopped')
    else:
        await change_work_statement({"work_statement": False})  # True - софт пашет | False - останавливается

        loguru.logger.info(f'UNIT:STOP: unit {uid} stopped')
        return web.Response(text='Unit stopped')


@routes.get('/unit/get_settings')
async def get_settings_get(request: Request):
    uid = request.app['uid']
    settings = await get_settings_data_from_db()
    settings = {
        'profit': settings['profit'],
        **settings['collections_parser']
    }
    loguru.logger.info(f'UNIT:GET_SETTINGS: unit {uid} getting settings')
    return web.json_response(settings)


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


@routes.post('/unit/set_settings')
async def set_settings_post(request: web.Request):
    uid = request.app['uid']
    settings = await request.post()
    try:
        if parameter := validate_settings(settings):
            return web.Response(status=409, text=f'Неправильно задан параметр {parameter}')

        await update_settings_database(
            {
                "collections_parser": {
                    "min_price": settings['min_price'],
                    "max_price": settings['max_price'],
                    "min_one_day_sellings": settings['min_one_day_sellings'],
                    "min_one_day_volume": settings['min_one_day_volume'],
                    "offer_difference_percent": settings['offer_difference_percent'],
                },
                "profit": settings['profit'],
            }
        )
        await set_proxies()

    except Exception as e:
        loguru.logger.error(f'UNIT:SET_SETTINGS: {uid} {str(e)}')
        return web.Response(status=500, text=str(e))
    loguru.logger.info(f'UNIT:SET_SETTINGS: {uid} settings updated successfully')
    return web.Response(text='Settings updated')


@routes.post('/unit/set_collections')
async def set_collections_post(request: web.Request):
    uid = request.app['uid']
    collections = await request.json()

    loguru.logger.error(f'SET COLLECTIONS IS NOT IMPLEMENTED YET:\t{collections=}')
    raise NotImplemented
    # todo: wait for backend to set collections
