import os
import sys

from aiohttp import web

from utils.unit import start_program, set_proxies

from routes.unit import routes as unit_routes


def main():
    app = web.Application()

    port = int(sys.argv[1])
    uid = int(os.path.basename(os.path.normpath(os.getcwd())))
    app['port'] = port
    app['uid'] = uid

    app.add_routes(unit_routes)

    app.on_startup.extend([start_program, set_proxies])
    web.run_app(app, port=port)


if __name__ == '__main__':
    main()
