import os
import random
import subprocess
from contextlib import suppress
from typing import Awaitable, Any

from aiohttp import web
import asyncio
import sys
import loguru

from utils.database import change_work_statement, get_data_from_db, get_settings_data_from_db, update_settings_database
from collections_parser.parser import collections_update_handler, collections_prices_handler
from bidder.bidder_client import work_client

routes = web.RouteTableDef()

unit_port = -1
unit_uid = int(os.path.basename(os.path.normpath(os.getcwd())))


@routes.get('/start')
async def start_get(request):
    is_running = await get_data_from_db()
    if is_running:
        loguru.logger.warning(f'UNIT:START: unit {unit_uid} is already running')
        return web.Response(status=200, text=f'Unit is already running')

    if os.path.getsize(f'proxies.txt') == 0:
        loguru.logger.error(f'UNIT:START: proxies.txt is empty')
        return web.Response(status=503, text=f'No proxies provided')

    await change_work_statement({"work_statement": True})  # True - софт пашет | False - останавливается
    await start_program()
    loguru.logger.info(f'UNIT:START: unit {unit_uid} started')

    return web.Response(text='Unit started')


@routes.get('/is_running')
async def is_running_get(request):
    is_running = await get_data_from_db()
    if is_running:
        loguru.logger.info(f'UNIT:IS_RUNNING: unit {unit_uid} is running')
        return web.Response(text='True')
    else:
        loguru.logger.info(f'UNIT:IS_RUNNING: unit {unit_uid} is not running')
        return web.Response(text='False')


@routes.get('/stop')
async def stop_get(request):
    loguru.logger.info('STOP')
    is_running = await get_data_from_db()
    if not is_running:
        loguru.logger.warning(f'UNIT:STOP: unit {unit_uid} is already stopped')
        return web.Response(status=409, text=f'Unit {unit_uid} is already stopped')
    else:
        await change_work_statement({"work_statement": False})  # True - софт пашет | False - останавливается

        loguru.logger.info(f'UNIT:STOP: unit {unit_uid} stopped')
        return web.Response(text='Unit stopped')


@routes.get('/get_settings')
async def get_settings_get(request):
    settings = await get_settings_data_from_db()
    settings = {
        'profit': settings['profit'],
        **settings['collections_parser']
    }
    loguru.logger.info(f'UNIT:GET_SETTINGS: unit {unit_uid} getting settings')
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


@routes.post('/set_settings')
async def set_settings_post(request: web.Request):
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
        loguru.logger.error(f'UNIT:SET_SETTINGS: {unit_uid} {str(e)}')
        return web.Response(status=500, text=str(e))
    loguru.logger.info(f'UNIT:SET_SETTINGS: {unit_uid} settings updated successfully')
    return web.Response(text='Settings updated')


async def start_program(app=None):
    # todo: UNCOMMENT ON PRODUCTION
    asyncio.create_task(collections_update_handler()),
    asyncio.create_task(collections_prices_handler()),
    # asyncio.create_task(work_client()),


async def set_proxies(app=None):
    with open('proxies.txt') as file:
        proxies = [row.strip() for row in file.readlines()]
    main_proxies = proxies[:2]
    proxies = proxies[2:]
    await update_settings_database(
        {
            "proxies": {
                "main": main_proxies,
                "parse_proxies": proxies  # из файла proxies.txt
            }
        }
    )


def main():
    global unit_port
    unit_port = int(sys.argv[1])

    app = web.Application()
    app.add_routes(routes)
    app.on_startup.extend([start_program, set_proxies])
    web.run_app(app, port=unit_port)


if __name__ == '__main__':
    main()
