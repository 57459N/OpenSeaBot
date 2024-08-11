import os

import loguru
from aiohttp import web
from aiohttp.web_request import Request

from server.misc import unit_exists, add_proxies
from server.user_info import UserInfo

routes = web.RouteTableDef()


@routes.get('/server/get_units_status')
async def get_units_status_handler(request: Request):
    data = {}
    for d in os.listdir('./units'):
        if not unit_exists(d) or not d.isdigit():
            continue
        data[d] = False

    data.update({k: v is not None for k, v in request.app['active_units'].items()})

    loguru.logger.info(f'SERVER:GET_UNITS_STATUS: sending units statuses')
    return web.json_response(data)


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
