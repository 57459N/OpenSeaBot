import asyncio
from concurrent.futures import ThreadPoolExecutor
import aiohttp
import random
import requests
from requests_client.utils.exceptions import BadStatusCode
from requests_client.utils.headers import DEFAULT_HEADERS

class RequestsClient:
    def __init__(self, proxies=None, headers=None):
        self.proxies = proxies or []
        self.headers = headers or DEFAULT_HEADERS
        self.session = None

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

    async def fetch_kwargs(self, **kwargs):
        kwargs.setdefault("proxy", random.choice(self.proxies) if self.proxies else None)
        kwargs.setdefault("timeout", aiohttp.ClientTimeout(total=10))
        
        if "headers" in kwargs:
            if isinstance(kwargs["headers"], dict):
                headers = self.headers.copy()
                headers.update(kwargs["headers"])
                kwargs["headers"] = headers
        else:
            kwargs["headers"] = self.headers

        return kwargs

    async def request(self, method, url, **kwargs):
        await self.open_session()
        kwargs = await self.fetch_kwargs(**kwargs)

        async with self.session.request(method.upper(), url, ssl=False, **kwargs) as response:
            if response.status == 200:
                return await response.json()
            else:
                response_text = await response.text()
                raise BadStatusCode(
                    f'[{url}:{method.upper()}] returned bad response code: {response.status}\nText: {response_text}'
                )

    async def request_without_response(self, method: str, url: str, **kwargs):
        await self.open_session()
        kwargs = await self.fetch_kwargs(**kwargs)

        async with self.session.request(method.upper(), url, ssl=False, **kwargs):
            pass  # We don't process the response

    async def async_request(self, method, url, **kwargs):
        loop = asyncio.get_event_loop()
        kwargs = await self.fetch_kwargs(**kwargs)

        def sync_request():
            response = requests.request(method=method, url=url, **kwargs)
            if response.status_code == 200:
                return response.json()
            else:
                raise BadStatusCode(
                    f'sync_request[{url}:{method.upper()}] returned bad response code: {response.status_code}\n'
                )

        with ThreadPoolExecutor() as pool:
            return await loop.run_in_executor(pool, sync_request)

