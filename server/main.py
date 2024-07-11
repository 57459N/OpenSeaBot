import asyncio
import time
from _datetime import datetime, timedelta
import logging
from contextlib import suppress

import aiohttp
from aiohttp import web
import sys
import os
from routes import routes
from misc import init_unit, Unit
from server import misc


async def daily_ctx(app: web.Application):
    task = asyncio.create_task(misc.daily_sub_balance_decrease(app))
    yield
    task.cancel()
    with suppress(asyncio.CancelledError):
        await task


def main():
    # init all units
    active_units: dict[str, Unit] = dict()

    if not os.path.exists('./units'):
        os.mkdir('./units')
    for uid in os.listdir('./units'):
        active_units[uid] = init_unit(uid)
    time.sleep(5)
    port = 8887
    if len(sys.argv) == 2:
        port = int(sys.argv[1])
    else:
        print(f'To specify another port use `{sys.argv[0]} <port>`')

    # start server
    app = web.Application()
    # to allow routes to use active units dict
    app['active_units'] = active_units
    app['port'] = port

    app.cleanup_ctx.append(daily_ctx)

    app.add_routes(routes)

    web.run_app(app, port=port)


if __name__ == '__main__':
    main()
