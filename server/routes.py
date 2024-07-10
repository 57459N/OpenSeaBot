import asyncio
import logging
import os
import sys
from dataclasses import asdict

from aiohttp import web
import aiohttp

from misc import create_unit, init_unit, get_userinfo, validate_token, unit_exists
from server import config
from server.user_info import UserInfo

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

routes = web.RouteTableDef()


# todo: move from start, stop and etc. lines with not found and uid check to separate middleware

@routes.get('/unit/create')
async def unit_create_get(request):
    uid = request.rel_url.query.get('uid', None)
    if uid is None:
        logging.warning(f'SERVER:CREATE_UNIT: bad request')
        return web.Response(status=400, text='Provide `uid` parameter into URL. For example: /unit/create?uid=1')

    try:
        await create_unit(uid)
        await asyncio.sleep(1)
        request.app['active_units'][uid] = init_unit(uid)
        await asyncio.sleep(1)
    except Exception as e:
        return web.Response(status=500, text=str(e))
    logging.info(f'SERVER:CREATE_UNIT: unit {uid} created')

    return web.Response(text='OK', status=201)


@routes.get('/unit/start')
async def unit_start(request):
    uid = request.rel_url.query.get('uid', None)
    if uid is None:
        logging.warning(f'SERVER:START_UNIT: bad request')
        return web.Response(status=400, text='Provide `uid` parameter into URL. For example: /unit/start?uid=1')

    if not unit_exists(uid):
        logging.warning(f'SERVER:START_UNIT: unit {uid} not found')
        return web.Response(status=404, text=f'Unit {uid} not found')

    active_units = request.app['active_units']
    if uid not in active_units.keys():
        logging.warning(f'SERVER:START_UNIT: unit {uid} is not initialized')
        return web.Response(status=409, text=f'Unit {uid} is not initialized')

    async with aiohttp.ClientSession() as session:
        url = f'http://localhost:{active_units[uid].port}/start'
        async with session.get(url) as resp:
            return web.Response(status=resp.status, text=await resp.text())


@routes.get('/unit/stop')
async def unit_stop(request):
    uid = request.rel_url.query.get('uid', None)
    if uid is None:
        logging.warning(f'SERVER:STOP_UNIT: bad request')
        return web.Response(status=400, text='Provide `uid` parameter into URL. For example: /unit/stop?uid=1')

    if not unit_exists(uid):
        logging.warning(f'SERVER:STOP_UNIT: unit {uid} not found')
        return web.Response(status=404, text=f'Unit {uid} not found')

    active_units = request.app['active_units']
    async with aiohttp.ClientSession() as session:
        url = f'http://localhost:{active_units[uid].port}/stop'
        async with session.get(url) as resp:
            return web.Response(status=resp.status, text=await resp.text())


@routes.get('/unit/get_settings')
async def get_settings(request):
    uid = request.rel_url.query.get('uid', None)
    if uid is None:
        logging.warning(f'SERVER:GET_SETTINGS: bad request')
        return web.Response(status=400, text='Provide `uid` parameter into URL. For example: /unit/get_settings?uid=1')

    if not unit_exists(uid):
        logging.warning(f'SERVER:GET_SETTINGS: unit {uid} not found')
        return web.Response(status=404, text=f'Unit {uid} not found')

    active_units = request.app['active_units']
    async with aiohttp.ClientSession() as session:
        url = f'http://localhost:{active_units[uid].port}/get_settings'
        async with session.get(url) as resp:
            return web.json_response(await resp.json(encoding='utf-8'))


@routes.get('/unit/set_settings')
async def set_settings(request):
    uid = request.rel_url.query.get('uid', None)
    if uid is None:
        logging.warning(f'SERVER:START_UNIT: bad request')
        return web.Response(status=400, text='Provide `uid` parameter into URL. For example: /unit/set_settings?uid=1')

    if not unit_exists(uid):
        logging.warning(f'SERVER:STOP_UNIT: unit {uid} not found')
        return web.Response(status=404, text=f'Unit {uid} not found')

    active_units = request.app['active_units']
    settings = dict(request.rel_url.query)
    settings.pop('uid')
    print(type(settings))
    async with aiohttp.ClientSession() as session:
        url = f'http://localhost:{active_units[uid].port}/set_settings'
        async with session.post(url, data=settings) as resp:
            return web.Response(status=resp.status, text=await resp.text())


@routes.get('/server/get_user_ids')
async def set_settings(request):
    user_ids = []
    for file in os.listdir('./units'):
        if os.path.isdir(f'./units/{file}') and file.isdigit():
            user_ids.append(file)

    return web.json_response({'user_ids': user_ids})


@routes.get('/user/increase_balance')
async def increase_user_balance(request):
    uid = request.rel_url.query.get('uid', None)
    amount = request.rel_url.query.get('amount', None)
    token = request.rel_url.query.get('token', None)
    if uid is None or amount is None or token is None:
        logging.warning(f'SERVER:INCREASE_USER_BALANCE: bad request')
        return web.Response(status=400,
                            text='Provide `uid`, `amount` and `token` parameters into URL.'
                                 ' For example: /user/increase_balance?uid=1&amount=10&token=123')

    if validate_token(token) is False:
        logging.error(f'SERVER:INCREASE_USER_BALANCE: bad token trying to increase balance for {uid}')
        return web.Response(status=401, text='Bad token')

    info_path = f'./units/{uid}/.userinfo'
    # User's unit is not created yet
    if not unit_exists(uid):
        dirs = info_path[:info_path.rfind('/')]
        os.makedirs(dirs, exist_ok=True)
        try:
            await create_unit(uid)
            request.app['active_units'][uid] = init_unit(uid)
        except Exception as e:
            logging.error(f'SERVER:FIRST_INCREASE_BALANCE: unit {uid} not created\n{e}')

    with UserInfo(uid) as ui:
        ui.balance += float(amount)

    logging.info(f'SERVER:INCREASE_USER_BALANCE: balance increased by {amount} to user {uid}')

    return web.Response(status=200, text='OK')


@routes.get('/user/get_info')
async def get_user_info_handler(request):
    uid = request.rel_url.query.get('uid', None)
    if uid is None:
        logging.warning(f'SERVER:GET_USER_INFO: bad request')
        return web.Response(status=400, text='Provide `uid` parameter into URL. For example: /user/get_info?uid=1')

    if not unit_exists(uid):
        logging.warning(f'SERVER:GET_USER_INFO: user {uid} not found')
        return web.Response(status=404, text=f'User {uid} not found')

    with UserInfo(uid) as ui:
        dict_ui = asdict(ui)
        dict_ui['days_left'] = dict_ui['balance'] // config.sub_cost
        return web.json_response(dict_ui)
