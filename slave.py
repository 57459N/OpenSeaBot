# slave.py
import random

from aiohttp import web
import asyncio
import sys
import logging

routes = web.RouteTableDef()

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

slave_id = -1


@routes.get('/id')
async def _id(request):
    return web.Response(text=str(slave_id))


@routes.post('/message')
async def message_post(request):
    data = await request.json()
    message = data['message']

    response = f"Slave {slave_id} processed: {message}"
    logging.info(f'MESSAGE: {message}')
    return web.json_response({'response': response})


@routes.get('/message')
async def message_get(request):
    message = request.rel_url.query.get('text', None)
    if message is None:
        logging.warning(f'MESSAGE: bad request')
        return web.Response(status=400, text='Provide `text` parameter into URL. For example: /message?text=Hello')
    else:
        logging.info(f'MESSAGE: {message}')
        return web.Response(text=f'Hello! You texted me:\n{message}')


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
    print(f'Running task{random.randint(0, 5) * "."}')


task = Task(simple_task, slave_id)


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
    global slave_id
    slave_id = int(sys.argv[1])

    app = web.Application()
    app.add_routes(routes)
    web.run_app(app, port=8888 + slave_id)


if __name__ == '__main__':
    main()
