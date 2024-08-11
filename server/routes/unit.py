import asyncio
import os
from dataclasses import asdict

import aiohttp
import loguru
from aiogram.utils.formatting import Code
from aiohttp import web, ClientResponseError
from aiohttp.web_request import Request
from eth_account import Account

import config
from encryption.system import decrypt_private_key, encrypt_private_key
from misc import unit_exists, init_unit, deinit_unit, delete_unit, create_unit, send_message_to_support, add_proxies
from user_info import UserInfo, UserStatus
from payments.system import manager as payments_manager

routes = web.RouteTableDef()


@routes.get('/unit/{uid}/init')
async def unit_init_handler(request: Request):
    uid = request.match_info.get('uid', None)
    if not unit_exists(uid):
        loguru.logger.warning(f'SERVER:INIT_UNIT: unit {uid} not found')
        return web.Response(status=404, text=f'Unit {uid} not found')

    if request.app['active_units'].get(uid):
        loguru.logger.warning(f'SERVER:INIT_UNIT: unit {uid} is already initialized')
        return web.Response(status=409, text=f'Unit {uid} is already initialized')

    try:
        request.app['active_units'][uid] = init_unit(uid)
        loguru.logger.info(f'SERVER:INIT_UNIT: unit {uid} initialized')
        return web.Response(text='OK', status=200)
    except Exception as e:
        loguru.logger.error(f'SERVER:INIT_UNIT: {e}')
        return web.Response(status=500, text=str(e))


@routes.get('/unit/{uid}/deinit')
async def unit_deinit_handler(request: Request):
    uid = request.match_info.get('uid', None)
    if not unit_exists(uid):
        loguru.logger.warning(f'SERVER:INIT_UNIT: unit {uid} not found')
        return web.Response(status=404, text=f'Unit {uid} not found')

    if uid not in request.app['active_units']:
        loguru.logger.warning(f'SERVER:INIT_UNIT: unit {uid} is not initialized')
        return web.Response(status=409, text=f'Unit {uid} is not initialized')

    unit = request.app['active_units'].pop(uid)
    try:
        deinit_unit(unit)
        loguru.logger.info(f'SERVER:DEINIT_UNIT: unit {unit.port} deinitialized')
        return web.Response()
    except Exception as e:
        loguru.logger.error(f'SERVER:DEINIT_UNIT: {e}')
        return web.Response(status=500, text=str(e))


@routes.get('/unit/{uid}/delete')
async def unit_delete_handler(request: Request):
    uid = request.match_info['uid']

    try:
        delete_unit(uid, request.app['active_units'])
        return web.Response(text='OK', status=200)
    except Exception as e:
        return web.Response(status=500, text=str(e))


@routes.get('/unit/{uid}/create')
async def unit_create_handler(request: Request):
    uid = request.match_info.get('uid', None)
    if uid is None:
        loguru.logger.warning(f'SERVER:CREATE_UNIT: bad request')
        return web.Response(status=400, text='Provide `uid` parameter into URL. For example: /unit/1/create')

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
        return web.Response(status=400, text='Provide `uid` parameter into URL. For example: /unit/1/start')

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
        url = f'http://localhost:{active_units[uid].port}/unit/start'
        async with session.get(url) as resp:
            return web.Response(status=resp.status, text=await resp.text())


@routes.get('/unit/{uid}/stop')
async def unit_stop_handler(request: Request):
    uid = request.match_info.get('uid', None)
    if uid is None:
        loguru.logger.warning(f'SERVER:STOP_UNIT: bad request')
        return web.Response(status=400, text='Provide `uid` parameter into URL. For example: /unit/1/stop')

    if not unit_exists(uid):
        loguru.logger.warning(f'SERVER:STOP_UNIT: unit {uid} not found')
        return web.Response(status=404, text=f'Unit {uid} not found')

    active_units = request.app['active_units']
    async with aiohttp.ClientSession() as session:
        url = f'http://localhost:{active_units[uid].port}/unit/stop'
        async with session.get(url) as resp:
            return web.Response(status=resp.status, text=await resp.text())


@routes.get('/unit/{uid}/get_settings')
async def get_settings_handler(request: Request):
    uid = request.match_info.get('uid', None)
    if uid is None:
        loguru.logger.warning(f'SERVER:GET_SETTINGS: bad request')
        return web.Response(status=400, text='Provide `uid` parameter into URL. For example: /unit/1/get_settings')

    if not unit_exists(uid):
        loguru.logger.warning(f'SERVER:GET_SETTINGS: unit {uid} not found')
        return web.Response(status=404, text=f'Unit {uid} not found')

    # todo: check if unit is initialized

    active_units = request.app['active_units']
    async with aiohttp.ClientSession() as session:
        url = f'http://localhost:{active_units[uid].port}/unit/get_settings'
        async with session.get(url) as resp:
            return web.json_response(await resp.json(encoding='utf-8'))


@routes.get('/unit/{uid}/set_settings')
async def set_settings_handler(request: Request):
    uid = request.match_info.get('uid', None)
    if uid is None:
        loguru.logger.warning(f'SERVER:START_UNIT: bad request')
        return web.Response(status=400, text='Provide `uid` parameter into URL. For example: /unit/1/set_settings')

    if not unit_exists(uid):
        loguru.logger.warning(f'SERVER:STOP_UNIT: unit {uid} not found')
        return web.Response(status=404, text=f'Unit {uid} not found')

    active_units = request.app['active_units']
    settings = dict(request.rel_url.query)
    if 'token' in settings:
        settings.pop('token')
    async with aiohttp.ClientSession() as session:
        url = f'http://localhost:{active_units[uid].port}/unit/set_settings'
        async with session.post(url, data=settings) as resp:
            return web.Response(status=resp.status, text=await resp.text())


@routes.post('/unit/{uid}/set_wallet_data')
async def set_wallet_data_handler(request: Request):
    uid = request.match_info.get('uid', None)
    if uid is None:
        loguru.logger.warning(f'SERVER:SET_WALLET_DATA: bad request')
        return web.Response(status=400, text='Provide `uid` parameter into URL. For example: /unit/1/set_wallet_data')

    if not unit_exists(uid):
        loguru.logger.warning(f'SERVER:SET_WALLET_DATA: unit {uid} not found')
        return web.Response(status=404, text=f'Unit {uid} not found')

    data = await request.json()
    if 'private_key' not in data:
        loguru.logger.warning(f'SERVER:SET_WALLET_DATA: bad request')
        return web.Response(status=400,
                            text='Provide `address` and `private_key` parameters into body. For example: {"address": "1", "private_key": "2"}')

    old_bot_wallet = None
    old_encrypted_pk = None
    new_pk = await decrypt_private_key(data['private_key'].encode(), config.BOT_API_TOKEN)

    try:
        with open(f'./units/{uid}/data/private_key.txt', 'rb') as f:
            old_encrypted_pk = f.read()

        with open(f'./units/{uid}/data/private_key.txt', 'wb') as f:
            encrypted = await encrypt_private_key(new_pk)
            f.write(encrypted)

        with UserInfo(f'./units/{uid}/.userinfo') as ui:
            old_bot_wallet = ui.bot_wallet
            acc = Account.from_key(new_pk)
            ui.bot_wallet = acc.address

    except Exception as e:
        if old_encrypted_pk is not None:
            loguru.logger.warning(f'SERVER:SET_WALLET_DATA: restoring private key {uid}')
            with open(f'./units/{uid}/data/private_key.txt', 'wb') as f:
                f.write(old_encrypted_pk)

        if old_bot_wallet is not None:
            loguru.logger.warning(f'SERVER:SET_WALLET_DATA: restoring bot wallet {uid}')
            with UserInfo(f'./units/{uid}/.userinfo') as ui:
                ui.bot_wallet = old_bot_wallet

        loguru.logger.error(f'SERVER:SET_WALLET_DATA: {e}')
        await send_message_to_support(f'Ошибка при обновлении кошелька пользователя {uid}.\n\n{e}')
        return web.Response(status=500, text=f'Error while updating wallet data to user {uid}\n{e}')

    return web.Response(status=200)


@routes.get('/unit/{uid}/get_private_key')
async def get_private_key_handler(request: Request):
    uid = request.match_info.get('uid', None)

    if not unit_exists(uid):
        loguru.logger.warning(f'SERVER:GET_PRIVATE_KEY: unit {uid} not found')
        return web.Response(status=404, text=f'Unit {uid} not found')

    with open(f'./units/{uid}/data/private_key.txt', 'rb') as f:
        pk = f.read()
    pk = await decrypt_private_key(pk)
    encrypted_to_send = await encrypt_private_key(pk, config.BOT_API_TOKEN)
    return web.json_response(encrypted_to_send.decode('utf-8'))


@routes.get('/user/{uid}/increase_balance')
async def increase_user_balance_handler(request: Request):
    uid = request.match_info.get('uid', None)
    amount = request.rel_url.query.get('amount', None)
    if uid is None or amount is None:
        loguru.logger.warning(f'SERVER:INCREASE_USER_BALANCE: bad request')
        return web.Response(status=400,
                            text='Provide `uid`, `amount` parameters into URL.'
                                 ' For example: /user/1/increase_balance?amount=10')
    try:
        amount = float(amount)
        a = int(uid)
    except ValueError:
        loguru.logger.warning(f'SERVER:INCREASE_USER_BALANCE: bad request')
        return web.Response(status=400,
                            text='`uid` must be an integer\n`amount` must be a number. 777 or 3.14'
                                 ' For example: /user/1/increase_balance?amount=10')

    # User's unit is not created yet
    if not unit_exists(uid):
        try:
            await create_unit(uid)
            request.app['active_units'][uid] = init_unit(uid)
        except Exception as e:
            loguru.logger.error(f'SERVER:FIRST_INCREASE_BALANCE: unit {uid} not fully created\n{e}')
            await send_message_to_support(f'User {Code(uid).as_html()}: {e}')

    with UserInfo(f'./units/{uid}/.userinfo') as ui:
        ui.increase_balance_and_activate(amount=amount)

    loguru.logger.info(f'SERVER:INCREASE_USER_BALANCE: balance increased by {amount} to user {uid}')

    return web.Response(status=200, text='OK')


@routes.get('/user/{uid}/give_days')
async def give_days_handler(request: Request):
    uid = request.match_info.get('uid', None)
    amount = request.rel_url.query.get('amount', None)
    # todo: add token validation
    if amount is None or not amount.isdigit():
        loguru.logger.warning(f'SERVER:GIVE_DAYS: bad request')
        return web.Response(status=400,
                            text='Provide `amount` parameter as number into URL. For example: /user/1/give_days?amount=10')

    if not unit_exists(uid):
        loguru.logger.warning(f'SERVER:STOP_UNIT: unit {uid} not found')
        return web.Response(status=404, text=f'Unit {uid} not found')

    if os.path.exists(f'./units/{uid}/.userinfo'):
        with UserInfo(f'./units/{uid}/.userinfo') as ui:
            ui.increase_balance_and_activate(amount=config.SUB_COST_DAY * int(amount))
            loguru.logger.info(f'SERVER:GIVE_DAYS: {amount} days given to user {uid}')
            return web.Response(status=200, text='OK')
    else:
        return web.Response(status=409, text=f'User {uid} config is not found.')


@routes.get('/user/{uid}/get_info')
async def get_user_info_handler(request: Request):
    uid = request.match_info.get('uid', None)
    if uid is None:
        loguru.logger.warning(f'SERVER:GET_USER_INFO: bad request')
        return web.Response(status=400, text='Provide `uid` parameter into URL. For example: /user/1/get_info')

    if not unit_exists(uid):
        return web.json_response({'activation_cost': config.SUB_COST_MONTH})

    with UserInfo(f'./units/{uid}/.userinfo') as ui:
        dict_ui = asdict(ui)
        dict_ui['days_left'] = dict_ui['balance'] // config.SUB_COST_DAY

        if ui.status == UserStatus.deactivated:
            dict_ui['activation_cost'] = config.SUB_COST_DAY
        elif ui.status == UserStatus.inactive:
            dict_ui['activation_cost'] = config.SUB_COST_MONTH

        try:
            balance = await payments_manager.fetch_bot_balance(ui.bot_wallet)
            dict_ui['bot_balance_eth'] = balance['eth']
            dict_ui['bot_balance_weth'] = balance['weth']
        except ClientResponseError:
            dict_ui['bot_balance_eth'] = 'Not loaded'
            dict_ui['bot_balance_weth'] = 'Not loaded'
        except ValueError:
            dict_ui['bot_balance_eth'] = 'Incorrect wallet format'
            dict_ui['bot_balance_weth'] = 'Incorrect wallet format'

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
    except ValueError:
        loguru.logger.warning(f'SERVER:ADD_IDLE_PROXIES: bad request')
        return web.Response(status=400, text='`proxies` must be a list of strings in json format')

    await add_proxies('./.idle_proxies', proxies)
    loguru.logger.info(f'SERVER:ADD_IDLE_PROXIES: {len(proxies)} proxies added')
    return web.Response()


@routes.post('/unit/{uid}/add_proxies')
async def add_unit_proxies_handler(request: Request):
    try:
        proxies = await request.json()
        if not isinstance(proxies, list):
            raise ValueError
        for el in proxies:
            if not isinstance(el, str):
                raise ValueError
    except ValueError:
        loguru.logger.warning(f'SERVER:ADD_UNIT_PROXIES: bad request')
        return web.Response(status=400, text='`proxies` must be a list of strings in json format')

    uid = request.match_info.get('uid', None)
    if not unit_exists(uid):
        loguru.logger.warning(f'SERVER:ADD_UNIT_PROXIES: unit {uid} not found')
        return web.Response(status=404, text=f'Unit {uid} not found')

    await add_proxies(f'./units/{uid}/proxies.txt', proxies)
    loguru.logger.info(f'SERVER:ADD_UNIT_PROXIES: {len(proxies)} proxies added to user {uid}')
    return web.Response()


@routes.get('/server/get_user_ids')
async def get_user_ids_handler(request: Request):
    status: str | None = request.rel_url.query.get('status', None)

    user_ids = []
    use_status = False
    if status is not None and status != '' and status.lower() != 'all':
        use_status = True
        status = status.capitalize()

    for file in os.listdir('./units'):
        if not os.path.isdir(f'./units/{file}') or not file.isdigit():
            continue

        with UserInfo(f'./units/{file}/.userinfo') as ui:
            if not use_status or ui.status == status:
                user_ids.append(file)

    return web.json_response({'user_ids': user_ids})
