import aiohttp
import loguru
from aiohttp import web
from aiohttp.web_request import Request

from server.misc import unit_exists, add_proxies
from server.user_info import UserInfo, UserStatus

routes = web.RouteTableDef()


@routes.get('/seller/{uid}/start')
async def unit_start_handler(request: Request):
    uid = request.match_info.get('uid', None)

    if not unit_exists(uid):
        loguru.logger.warning(f'SERVER:START_UNIT: unit {uid} not found')
        return web.Response(status=404, text=f'Unit {uid} not found')

    active_units = request.app['active_units']
    if uid not in active_units.keys() or active_units[uid] is None:
        loguru.logger.warning(f'SERVER:START_UNIT: unit {uid} is not initialized')
        return web.Response(status=409, text=f'Unit {uid} is not initialized')

    with UserInfo(f'./units/{uid}/.userinfo') as ui:
        if ui.status != UserStatus.active:
            loguru.logger.warning(f'SERVER:START_UNIT: subscription of user {uid} is not active')
            return web.Response(status=403, text=f'subscription of user {uid} is not active')

    async with aiohttp.ClientSession() as session:
        url = f'http://localhost:{active_units[uid].port}/seller/start'
        async with session.get(url) as resp:
            return web.Response(status=resp.status, text=await resp.text())


@routes.get('/seller/{uid}/stop')
async def unit_stop_handler(request: Request):
    uid = request.match_info.get('uid', None)
    if not unit_exists(uid):
        loguru.logger.warning(f'SERVER:STOP_UNIT: unit {uid} not found')
        return web.Response(status=404, text=f'Unit {uid} not found')

    active_units = request.app['active_units']
    async with aiohttp.ClientSession() as session:
        url = f'http://localhost:{active_units[uid].port}/seller/stop'
        async with session.get(url) as resp:
            return web.Response(status=resp.status, text=await resp.text())


@routes.get('/seller/{uid}/get_settings')
async def get_settings_handler(request: Request):
    uid = request.match_info.get('uid', None)
    if not unit_exists(uid):
        loguru.logger.warning(f'SERVER:GET_SETTINGS: unit {uid} not found')
        return web.Response(status=404, text=f'Unit {uid} not found')

    # todo: check if unit is initialized

    active_units = request.app['active_units']
    async with aiohttp.ClientSession() as session:
        url = f'http://localhost:{active_units[uid].port}/seller/get_settings'
        async with session.get(url) as resp:
            return web.json_response(await resp.json(encoding='utf-8'))


@routes.get('/seller/{uid}/set_settings')
async def set_settings_handler(request: Request):
    uid = request.match_info.get('uid', None)

    if not unit_exists(uid):
        loguru.logger.warning(f'SERVER:SET_SETTINGS: unit {uid} not found')
        return web.Response(status=404, text=f'Unit {uid} not found')

    active_units = request.app['active_units']
    settings = dict(request.rel_url.query)
    if 'token' in settings:
        settings.pop('token')
    async with aiohttp.ClientSession() as session:
        url = f'http://localhost:{active_units[uid].port}/seller/set_settings'
        async with session.post(url, data=settings) as resp:
            return web.Response(status=resp.status, text=await resp.text())
