import aiohttp
import loguru
from aiohttp import web
from aiohttp.web_request import Request

from server.misc import unit_exists
from server.user_info import UserStatus, UserInfo

routes = web.RouteTableDef()


@routes.get("/scanner/{uid}/start")
async def start_scanner(request: Request):
    uid = request.match_info.get("uid")

    if not unit_exists(uid):
        loguru.logger.warning(f'SERVER:START_SCANNER: unit {uid} not found')
        return web.Response(status=404, text=f'Unit {uid} not found')

    active_units = request.app['active_units']
    if uid not in active_units.keys() or active_units[uid] is None:
        loguru.logger.warning(f'SERVER:START_SCANNER: unit {uid} is not initialized')
        return web.Response(status=409, text=f'Unit {uid} is not initialized')

    with UserInfo(f'./units/{uid}/.userinfo') as ui:
        if ui.status != UserStatus.active:
            loguru.logger.warning(f'SERVER:START_SCANNER: subscription of user {uid} is not active')
            return web.Response(status=403, text=f'subscription of user {uid} is not active')

    # todo: get scan data from unit
    # async with aiohttp.ClientSession() as session:
    #     url = f'http://localhost:{active_units[uid].port}/scan'
    #     async with session.get(url) as resp:
    #         return web.Response(status=resp.status, text=await resp.text())


@routes.get('/scanner/{uid}/get_settings')
async def get_settings_scanner(request: Request):
    uid = request.match_info.get('uid', None)
    if uid is None:
        loguru.logger.warning(f'SERVER:GET_SETTINGS:SCANNER: bad request')
        return web.Response(status=400, text='Provide `uid` parameter into URL. For example: /unit/1/get_settings')

    if not unit_exists(uid):
        loguru.logger.warning(f'SERVER:GET_SETTINGS:SCANNER: unit {uid} not found')
        return web.Response(status=404, text=f'Unit {uid} not found')

    active_units = request.app['active_units']
    async with aiohttp.ClientSession() as session:
        url = f'http://localhost:{active_units[uid].port}/scanner/get_settings'
        async with session.get(url) as resp:
            return web.json_response(await resp.json(encoding='utf-8'))


@routes.get('/scanner/{uid}/set_settings')
async def set_settings_scanner(request: Request):
    uid = request.match_info.get('uid', None)
    if uid is None:
        loguru.logger.warning(f'SERVER:SET_SETTINGS:SCANNER: bad request')
        return web.Response(status=400, text='Provide `uid` parameter into URL. For example: /unit/1/set_settings')

    if not unit_exists(uid):
        loguru.logger.warning(f'SERVER:SET_SETTINGS:SCANNER: unit {uid} not found')
        return web.Response(status=404, text=f'Unit {uid} not found')

    active_units = request.app['active_units']
    settings = dict(request.rel_url.query)
    if 'token' in settings:
        settings.pop('token')
    async with aiohttp.ClientSession() as session:
        url = f'http://localhost:{active_units[uid].port}/scanner/set_settings'
        async with session.post(url, data=settings) as resp:
            return web.Response(status=resp.status, text=await resp.text())
