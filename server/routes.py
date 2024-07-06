import asyncio
import logging
import os
import sys

from aiohttp import web
import aiohttp

from all_later_separate import get_private_key, get_proxies, create_unit
from misc import init_unit

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

routes = web.RouteTableDef()


@routes.get('/unit/create')
async def unit_create_get(request):
    uid = request.rel_url.query.get('uid', None)
    if uid is None:
        logging.warning(f'SERVER:CREATE_UNIT: bad request')
        return web.Response(status=400, text='Provide `uid` parameter into URL. For example: /unit/create?uid=1')

    try:
        key = await get_private_key(uid)
        proxies = await get_proxies(uid)
        await create_unit(uid, key, proxies)
        await asyncio.sleep(1)
        init_unit(uid)
        await asyncio.sleep(1)

    except Exception as e:
        return web.Response(status=500, text=str(e))
    logging.info(f'SERVER:CREATE_UNIT: unit {uid} created')
    return web.Response(text='OK', status=201)


@routes.get('/unit/start')
async def unit_start_get(request):
    uid = request.rel_url.query.get('uid', None)
    if uid is None:
        logging.warning(f'SERVER:START_UNIT: bad request')
        return web.Response(status=400, text='Provide `uid` parameter into URL. For example: /unit/create?uid=1')

    if uid not in os.listdir('./units'):
        logging.warning(f'SERVER:START_UNIT: unit {uid} not found')
        return web.Response(status=404, text=f'Unit {uid} not found')

    active_units = request.app['active_units']
    if uid not in active_units.keys():
        logging.warning(f'SERVER:START_UNIT: unit {uid} is not initialized')
        return web.Response(status=409, text=f'Unit {uid} is not initialized')

    async with aiohttp.ClientSession() as session:
        url = f'http://localhost:{active_units[uid].port}/start'
        async with session.get(url) as resp:
            if resp.status != 200:
                logging.warning(f'SERVER:START_UNIT: unit {uid} not started')
                return web.Response(status=500, text=f'Unit {uid} not started')
            else:
                logging.info(f'SERVER:START_UNIT: unit {uid} started')
                return web.Response(text='OK', status=200)


@routes.get('/unit/stop')
async def unit_stop(request):
    uid = request.rel_url.query.get('uid', None)
    if uid is None:
        logging.warning(f'SERVER:START_UNIT: bad request')
        return web.Response(status=400, text='Provide `uid` parameter into URL. For example: /unit/create?uid=1')

    if uid not in os.listdir('./units'):
        logging.warning(f'SERVER:STOP_UNIT: unit {uid} not found')
        return web.Response(status=404, text=f'Unit {uid} not found')

    active_units = request.app['active_units']
    if uid not in active_units.keys():
        logging.warning(f'SERVER:STOP_UNIT: unit {uid} is not running')
        return web.Response(status=409, text=f'Unit {uid} is not running')

    async with aiohttp.ClientSession() as session:
        url = f'http://localhost:{active_units[uid].port}/stop'
        async with session.get(url) as resp:
            if resp.status != 200:
                logging.warning(f'SERVER:STOP_UNIT: unit {uid} not stopped')
                return web.Response(status=500, text=f'Unit {uid} not stopped')
            else:
                logging.info(f'SERVER:STOP_UNIT: unit {uid} stopped')
                return web.Response(text='OK', status=200)
