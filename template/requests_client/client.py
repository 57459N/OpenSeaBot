import asyncio
from concurrent.futures import ThreadPoolExecutor
import aiohttp
import random
import requests
from requests_client.utils.exceptions import BadStatusCode
from requests_client.utils.headers import DEFAULT_HEADERS

class RequestsClient:
    def __init__(self, proxy=None, headers=None):
        self.proxies = proxy or []
        self.headers = headers or DEFAULT_HEADERS
        self.session = None

        self.sync_session = requests.Session()

    async def open_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession(trust_env=True)

    async def close_session(self):
        if self.session:
            await self.session.close()
            self.session = None

    async def get_cookies(self):
        if self.session:
            return {cookie.key: cookie.value for cookie in self.session.cookie_jar}
        return {}

    async def fetch_kwargs(self, sync_request: bool = False, **kwargs):
        if not kwargs.get("proxy"):
            kwargs["proxy"] = random.choice(self.proxies)

        if not kwargs.get("timeout"):
            kwargs["timeout"] = 10

        if "headers" in kwargs.keys():
            if type(kwargs["headers"]) is dict:
                kwargs["headers"].update(self.headers)
        else:
            kwargs["headers"] = self.headers

        if sync_request and kwargs["proxy"]:
            kwargs["proxies"] = {
                "http": kwargs["proxy"],
                "https": kwargs["proxy"]
            }
            del kwargs["proxy"]

        return kwargs

    async def request(self, method, url, **kwargs):
        await self.open_session()
        kwargs = await self.fetch_kwargs(**kwargs)

        async with self.session.request(method.upper(), url, ssl=False, **kwargs) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise BadStatusCode(
                    f'[{url}:{method.upper()}] returned bad response code: {response.status}'
                )

    async def request_without_response(self, method: str, url: str, **kwargs):
        await self.open_session()
        kwargs = await self.fetch_kwargs(**kwargs)

        async with self.session.request(method.upper(), url, ssl=False, **kwargs):
            pass  # We don't process the response

    async def async_request(self, method, url, **kwargs):
        loop = asyncio.get_event_loop()
        kwargs = await self.fetch_kwargs(sync_request=True, **kwargs)

        def sync_request():
            response = self.sync_session.request(method=method, url=url, **kwargs)
            if response.status_code == 200:
                return response.json()
            else:
                raise BadStatusCode(
                    f'sync_request[{url}:{method.upper()}] returned bad response code: {response.status_code}\n'
                )

        with ThreadPoolExecutor() as pool:
            return await loop.run_in_executor(pool, sync_request)

