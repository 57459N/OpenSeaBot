import asyncio
import time
from contextlib import suppress

from aiohttp import web
import sys
import os

sys.path.append(os.getcwd())

from aiohttp.web_request import Request

from server.misc import init_unit, Unit, daily_sub_balance_decrease, validate_token
from routes.server import routes as server_routes
from routes.unit import routes as unit_routes
from routes.user import routes as user_routes


async def daily_ctx(app: web.Application):
    task = asyncio.create_task(daily_sub_balance_decrease(app))
    yield
    task.cancel()
    with suppress(asyncio.CancelledError):
        await task


@web.middleware
async def auth_middleware(request: Request, handler):
    token = request.rel_url.query.get('token')
    if token is None or not validate_token(token):
        return web.Response(status=401)
    else:
        return await handler(request)


def main():
    # init all units
    active_units: dict[str, Unit] = dict()

    if not os.path.exists('./units'):
        os.mkdir('./units')
    try:
        for uid in os.listdir('./units'):
            active_units[uid] = init_unit(uid)
    except Exception:
        pass

    time.sleep(5)
    port = 8887
    if len(sys.argv) == 2:
        port = int(sys.argv[1])
    else:
        print(f'To specify another port use `{sys.argv[0]} <port>`')

    # start server
    app = web.Application(middlewares=[auth_middleware])
    # to allow routes to use active units dict
    app['active_units'] = active_units
    app['port'] = port

    app.cleanup_ctx.append(daily_ctx)

    app.add_routes(server_routes)
    app.add_routes(user_routes)
    app.add_routes(unit_routes)

    web.run_app(app, port=port)


if __name__ == '__main__':
    main()
