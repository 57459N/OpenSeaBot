import os
import random
from contextlib import suppress
from typing import Awaitable

from aiohttp import web
import asyncio
import sys
import logging

from utils.database import change_work_statement, get_data_from_db, get_settings_data_from_db
from collections_parser.parser import collections_update_handler, collections_prices_handler
from bidder.bidder_client import work_client

routes = web.RouteTableDef()

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

unit_port = -1
unit_uid = int(os.getcwd().split('\\')[-1])


@routes.get('/start')
async def start_get(request):
    is_running = await get_data_from_db()
    if is_running:
        logging.warning(f'UNIT: unit {unit_uid} is already running')
        return web.Response(status=409, text=f'Unit {unit_uid} is already running')

    await change_work_statement({"work_statement": True})  # True - софт пашет | False - останавливается
    await start_program()
    logging.info(f'UNIT: unit {unit_uid} started')

    return web.Response(text='Unit started')


@routes.get('/stop')
async def stop_get(request):
    logging.info('STOP')
    is_running = await get_data_from_db()
    if not is_running:
        logging.warning(f'UNIT: unit {unit_uid} is not running')
        return web.Response(status=409, text=f'Unit {unit_uid} is not running')
    else:
        await change_work_statement({"work_statement": False})  # True - софт пашет | False - останавливается

        logging.info(f'UNIT: unit {unit_uid} stopped')
        return web.Response(text='Unit stopped')


@routes.get('/get_settings')
async def get_settings_get(request):
    settings = await get_settings_data_from_db()
    settings = {
        'profit': settings['profit'],
        **settings['collections_parser']
    }
    return web.json_response(settings)


async def start_program(app=None):
    # todo: UNCOMMENT ON PRODUCTION
    asyncio.create_task(collections_update_handler()),
    asyncio.create_task(collections_prices_handler()),
    # asyncio.create_task(work_client()),


def main():
    global unit_port
    unit_port = int(sys.argv[1])

    app = web.Application()
    app.add_routes(routes)
    app.on_startup.append(start_program)
    web.run_app(app, port=unit_port)


if __name__ == '__main__':
    main()
