from aiohttp import web
import sys
import os
from routes import routes
from misc import init_unit


def main():
    # init all units
    active_units = dict()
    for uid in os.listdir('./units'):
        active_units[uid] = init_unit(uid)

    port = 8887
    if len(sys.argv) == 2:
        port = int(sys.argv[1])
    else:
        print(f'To specify another port use `{sys.argv[0]} <port>`')
    print(f'Starting server on port {port}')
    # start server
    app = web.Application()
    # to allow routes to use active units dict
    app['active_units'] = active_units

    app.add_routes(routes)
    web.run_app(app, port=port)


if __name__ == '__main__':
    main()
