import asyncio
from _datetime import datetime, timedelta
import logging

from aiohttp import web
import sys
import os
from routes import routes
from misc import init_unit
from server import misc, config
from server.user_info import UserInfo


async def daily_sub_balance_decrease(app: web.Application):
    while True:
        now = datetime.now()
        midnight = datetime.combine(now.date() + timedelta(days=1), datetime.min.time())
        seconds_until_midnight = 10  # (midnight - now).total_seconds()
        logging.info(
            f"SERVER:DAILY_SUB_BALANCE_DECREASE: sleeping {seconds_until_midnight} seconds till next tax collection")
        await asyncio.sleep(seconds_until_midnight)

        for uid in os.listdir('./units'):
            if not os.path.isdir(f'./units/{uid}'):
                continue

            try:
                with UserInfo(f'./units/{uid}/.userinfo') as ui:
                    ui.decrease_balance_or_deactivate(config.sub_cost)
                    logging.info(f"SERVER:DAILY_SUB_BALANCE_DECREASE: {uid} sub is paid")
            except ValueError as e:
                logging.warning(
                    f"SERVER:DAILY_SUB_BALANCE_DECREASE: {uid} directory doesn't contain .userinfo file\n{e}")


def main():
    # init all units
    active_units = dict()

    if not os.path.exists('./units'):
        os.mkdir('./units')
    for uid in os.listdir('./units'):
        active_units[uid] = init_unit(uid)

    port = 8887
    if len(sys.argv) == 2:
        port = int(sys.argv[1])
    else:
        print(f'To specify another port use `{sys.argv[0]} <port>`')

    # start server
    app = web.Application()
    # to allow routes to use active units dict
    app['active_units'] = active_units

    # app.on_startup.append(daily_sub_balance_decrease)

    app.add_routes(routes)

    web.run_app(app, port=port)


if __name__ == '__main__':
    main()
