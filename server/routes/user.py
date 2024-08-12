import os
from dataclasses import asdict

import loguru
from aiogram.utils.formatting import Code
from aiohttp import web, ClientResponseError
from aiohttp.web_request import Request

import config
from payments.system import manager as payments_manager
from server.misc import unit_exists, create_unit, init_unit, send_message_to_support
from server.user_info import UserInfo, UserStatus

routes = web.RouteTableDef()


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

    with UserInfo(f'./units/{uid}/.userinfo') as ui:
        is_activated = ui.increase_balance_and_activate(amount=amount)
        balance = ui.balance

    if is_activated and not unit_exists(uid):
        try:
            await create_unit(uid)
            request.app['active_units'][uid] = init_unit(uid)
        except Exception as e:
            loguru.logger.error(f'SERVER:FIRST_INCREASE_BALANCE: unit {uid} not fully created\n{e}')
            await send_message_to_support(f'User {Code(uid).as_html()}: {e}')

    loguru.logger.info(f'SERVER:INCREASE_USER_BALANCE: balance increased by {amount} to user {uid}')

    return web.Response(status=200, text=str(balance))


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

    info_path = f'./units/{uid}/.userinfo'

    with UserInfo(info_path, create=True) as ui:
        ui.uid = int(uid)
        dict_ui = asdict(ui)
        dict_ui['days_left'] = dict_ui['balance'] // config.SUB_COST_DAY

        if ui.status == UserStatus.deactivated:
            dict_ui['activation_cost'] = config.SUB_COST_DAY
        elif ui.status == UserStatus.inactive or not unit_exists(uid):
            dict_ui['activation_cost'] = config.SUB_COST_MONTH

        try:
            if ui.bot_wallet == '':
                raise ValueError

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
