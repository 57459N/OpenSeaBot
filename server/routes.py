import asyncio
import loguru
import os
import sys
from dataclasses import asdict

from aiohttp import web
import aiohttp
from aiohttp.web_request import Request

from misc import create_unit, init_unit, validate_token, unit_exists, send_message_to_support, get_wallet_balance, \
    add_proxies
import config
from server.user_info import UserInfo, UserStatus


routes = web.RouteTableDef()


@routes.get('/unit/{uid}/create')
async def unit_create_handler(request: Request):
    uid = request.match_info.get('uid', None)
    if uid is None:
        loguru.logger.warning(f'SERVER:CREATE_UNIT: bad request')
        return web.Response(status=400, text='Provide `uid` parameter into URL. For example: /unit/create?uid=1')

    try:
        await create_unit(uid)
        await asyncio.sleep(1)
        request.app['active_units'][uid] = init_unit(uid)
        await asyncio.sleep(1)
    except Exception as e:
        return web.Response(status=500, text=str(e))
    loguru.logger.info(f'SERVER:CREATE_UNIT: unit {uid} created')

    return web.Response(text='OK', status=201)


@routes.get('/unit/{uid}/start')
async def unit_start_handler(request: Request):
    uid = request.match_info.get('uid', None)
    if uid is None:
        loguru.logger.warning(f'SERVER:START_UNIT: bad request')
        return web.Response(status=400, text='Provide `uid` parameter into URL. For example: /unit/start?uid=1')

    if not unit_exists(uid):
        loguru.logger.warning(f'SERVER:START_UNIT: unit {uid} not found')
        return web.Response(status=404, text=f'Unit {uid} not found')

    active_units = request.app['active_units']
    if uid not in active_units.keys():
        loguru.logger.warning(f'SERVER:START_UNIT: unit {uid} is not initialized')
        return web.Response(status=409, text=f'Unit {uid} is not initialized')

    with UserInfo(f'./units/{uid}/.userinfo') as ui:
        if ui.status != UserStatus.active:
            loguru.logger.warning(f'SERVER:START_UNIT: subscription of user {uid} is not active')
            return web.Response(status=403, text=f'subscription of user {uid} is not active')

    async with aiohttp.ClientSession() as session:
        url = f'http://localhost:{active_units[uid].port}/start'
        async with session.get(url) as resp:
            return web.Response(status=resp.status, text=await resp.text())


@routes.get('/unit/{uid}/stop')
async def unit_stop_handler(request: Request):
    uid = request.match_info.get('uid', None)
    if uid is None:
        loguru.logger.warning(f'SERVER:STOP_UNIT: bad request')
        return web.Response(status=400, text='Provide `uid` parameter into URL. For example: /unit/stop?uid=1')

    if not unit_exists(uid):
        loguru.logger.warning(f'SERVER:STOP_UNIT: unit {uid} not found')
        return web.Response(status=404, text=f'Unit {uid} not found')

    active_units = request.app['active_units']
    async with aiohttp.ClientSession() as session:
        url = f'http://localhost:{active_units[uid].port}/stop'
        async with session.get(url) as resp:
            return web.Response(status=resp.status, text=await resp.text())


@routes.get('/unit/{uid}/get_settings')
async def get_settings_handler(request: Request):
    uid = request.match_info.get('uid', None)
    if uid is None:
        loguru.logger.warning(f'SERVER:GET_SETTINGS: bad request')
        return web.Response(status=400, text='Provide `uid` parameter into URL. For example: /unit/get_settings?uid=1')

    if not unit_exists(uid):
        loguru.logger.warning(f'SERVER:GET_SETTINGS: unit {uid} not found')
        return web.Response(status=404, text=f'Unit {uid} not found')

    active_units = request.app['active_units']
    async with aiohttp.ClientSession() as session:
        url = f'http://localhost:{active_units[uid].port}/get_settings'
        async with session.get(url) as resp:
            return web.json_response(await resp.json(encoding='utf-8'))


@routes.get('/unit/{uid}/set_settings')
async def set_settings_handler(request: Request):
    uid = request.match_info.get('uid', None)
    if uid is None:
        loguru.logger.warning(f'SERVER:START_UNIT: bad request')
        return web.Response(status=400, text='Provide `uid` parameter into URL. For example: /unit/set_settings?uid=1')

    if not unit_exists(uid):
        loguru.logger.warning(f'SERVER:STOP_UNIT: unit {uid} not found')
        return web.Response(status=404, text=f'Unit {uid} not found')

    active_units = request.app['active_units']
    settings = dict(request.rel_url.query)
    async with aiohttp.ClientSession() as session:
        url = f'http://localhost:{active_units[uid].port}/set_settings'
        async with session.post(url, data=settings) as resp:
            return web.Response(status=resp.status, text=await resp.text())


@routes.get('/user/{uid}/increase_balance')
async def increase_user_balance_handler(request: Request):
    uid = request.match_info.get('uid', None)
    amount = request.rel_url.query.get('amount', None)
    token = request.rel_url.query.get('token', None)
    if uid is None or amount is None or token is None:
        loguru.logger.warning(f'SERVER:INCREASE_USER_BALANCE: bad request')
        return web.Response(status=400,
                            text='Provide `uid`, `amount` and `token` parameters into URL.'
                                 ' For example: /user/increase_balance?uid=1&amount=10&token=123')
    try:
        amount = float(amount)
        a = int(uid)
    except ValueError:
        loguru.logger.warning(f'SERVER:INCREASE_USER_BALANCE: bad request')
        return web.Response(status=400,
                            text='`uid` must be an integer\n`amount` must be a number. 777 or 3.14'
                                 ' For example: /user/increase_balance?uid=1&amount=10&token=123')

    if validate_token(token) is False:
        loguru.logger.error(f'SERVER:INCREASE_USER_BALANCE: bad token trying to increase balance for {uid}')
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
            loguru.logger.error(f'SERVER:FIRST_INCREASE_BALANCE: unit {uid} not created\n{e}')
            await send_message_to_support(e)

    with UserInfo(info_path) as ui:
        ui.increase_balance_and_activate(amount)

    loguru.logger.info(f'SERVER:INCREASE_USER_BALANCE: balance increased by {amount} to user {uid}')

    return web.Response(status=200, text='OK')


@routes.get('/user/{uid}/get_info')
async def get_user_info_handler(request: Request):
    uid = request.match_info.get('uid', None)
    if uid is None:
        loguru.logger.warning(f'SERVER:GET_USER_INFO: bad request')
        return web.Response(status=400, text='Provide `uid` parameter into URL. For example: /user/get_info?uid=1')

    if not unit_exists(uid):
        loguru.logger.warning(f'SERVER:GET_USER_INFO: user {uid} not found')
        return web.Response(status=404, text=f'User {uid} not found')

    with UserInfo(f'./units/{uid}/.userinfo') as ui:
        dict_ui = asdict(ui)
        dict_ui['days_left'] = dict_ui['balance'] // config.SUB_COST
        dict_ui['bot_balance'] = await get_wallet_balance(ui.const_bot_wallet)

    return web.json_response(dict_ui)


@routes.post('/server/add_proxies')
async def add_idle_proxies_handler(request: Request):
    try:
        proxies = await request.json()
        if not isinstance(proxies, list):
            raise ValueError
        for el in proxies:
            if not isinstance(el, str):
                raise ValueError
    except Exception:
        loguru.logger.warning(f'SERVER:ADD_IDLE_PROXIES: bad request')
        return web.Response(status=400, text='`proxies` must be a list of strings in json format')

    await add_proxies('./idle_proxies', proxies)
    loguru.logger.info(f'SERVER:ADD_IDLE_PROXIES: {len(proxies)} proxies added')
    return web.Response()


@routes.get('/server/get_user_ids')
async def get_user_ids_handler(request: Request):
    user_ids = []
    for file in os.listdir('./units'):
        if os.path.isdir(f'./units/{file}') and file.isdigit():
            user_ids.append(file)

    return web.json_response({'user_ids': user_ids})
