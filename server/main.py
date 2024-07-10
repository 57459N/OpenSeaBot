import logging

from aiohttp import web
import sys
import os
from routes import routes
from misc import init_unit
from server import misc, config
from server.user_info import UserInfo, UserStatus


async def daily_sub_update():
    for uid in os.listdir('./units'):
        if not os.path.isdir(f'./units/{uid}'):
            continue
        try:
            with UserInfo(uid) as ui:
                if ui.status == UserStatus.active:
                    if ui.balance < config.sub_cost:
                        ui.status = UserStatus.inactive
                    else:
                        ui.balance -= config.sub_cost
        except Exception as e:
            logging.error(f'SERVER:DAILY_SUB_UPDATE: uid {uid} is not an int')
            continue


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

    app.add_routes(routes)
    web.run_app(app, port=port)


if __name__ == '__main__':
    main()
