import os

from aiohttp import web
import asyncio
import sys
import logging
from all_later_separate import *

routes = web.RouteTableDef()

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

active_units = dict()


@routes.get('/unit/create')
async def unit_create_get(request):
    uid = request.rel_url.query.get('uid', None)
    if uid is None:
        logging.warning(f'SERVER:CREATE_UNIT: bad request')
        return web.Response(status=400, text='Provide `uid` parameter into URL. For example: /unit/create?uid=1')

    try:
        key = await get_private_key(uid)
        proxies = await get_proxies()
        await create_unit(uid, key, proxies)
    except Exception as e:
        return web.Response(status=500, text=str(e))

    return web.Response(text='OK', status=201)


@routes.get('/unit/start')
async def unit_start_get(request):
    uid = request.rel_url.query.get('uid', None)
    if uid is None:
        logging.warning(f'SERVER:START_UNIT: bad request')
        return web.Response(status=400, text='Provide `uid` parameter into URL. For example: /unit/create?uid=1')

    if uid not in os.listdir('..'):
        logging.warning(f'SERVER:START_UNIT: unit {uid} not found')
        return web.Response(status=404, text=f'Unit {uid} not found')



    return web.Response(text='OK', status=200)


# @routes.get('/unit/stop')
# async def unit_stop_get(request):
#     uid = request.rel_url.query.get('uid', None)
#     if uid is None:
#         logging.warning(f'SERVER:CREATE_UNIT: bad request')
#         return web.Response(status=400, text='Provide `uid` parameter into URL. For example: /unit/create?uid=1')
#
#     try:
#         key = await get_private_key(uid)
#         proxies = await get_proxies()
#         await create_unit(uid, key, proxies)
#     except Exception as e:
#         return web.Response(status=500, text=str(e))
#
#     return web.Response(text='OK', status=201)


def main():
    app = web.Application()
    app.add_routes(routes)
    web.run_app(app, port=8887)


if __name__ == '__main__':
    main()
