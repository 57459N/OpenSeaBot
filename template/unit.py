import random

from aiohttp import web
import asyncio
import sys
import logging

routes = web.RouteTableDef()

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

unit_id = -1


@routes.get('/id')
async def _id(request):
    return web.Response(text=str(unit_id))


class Task:
    def __init__(self, func: callable, *args, **kwargs):
        self._running = False
        self.func = func
        self.args = args
        self.kwargs = kwargs

    async def run(self):
        self._running = True
        while self.running:
            self.func(*self.args, *self.kwargs)
            await asyncio.sleep(1)

    def stop(self):
        self._running = False

    @property
    def running(self):
        return self._running


def simple_task(_id: int):
    print(f'Unit {unit_id} running task{random.randint(0, 5) * "."}')


task = Task(simple_task, unit_id)


@routes.get('/start')
async def start_get(request):
    global task
    logging.info('START')

    if not task.running:
        asyncio.create_task(task.run())
        return web.Response(text='OK')
    else:
        return web.Response(text='Already running')


@routes.get('/stop')
async def stop_get(request):
    global task
    logging.info('STOP')
    task.stop()
    return web.Response(text='OK')


def main():
    global unit_id
    unit_id = int(sys.argv[1])

    app = web.Application()
    app.add_routes(routes)
    web.run_app(app, port=8888 + unit_id)


if __name__ == '__main__':
    main()
