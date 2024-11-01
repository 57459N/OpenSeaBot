import asyncio
from concurrent.futures import ThreadPoolExecutor
import aiohttp
import random
import requests
from requests_client.utils.exceptions import BadStatusCode
from requests_client.utils.headers import DEFAULT_HEADERS

class RequestsClient:
    def __init__(self, proxy=None, headers=None, server_url: str = "http://localhost:8080/proxy-request"):
        self.proxies = proxy or []
        self.headers = headers or DEFAULT_HEADERS
        self.session = None
        self.server_url = server_url

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
        if not kwargs.get("proxy"):
            kwargs["proxy"] = random.choice(self.proxies)

        if not kwargs.get("timeout"):
            kwargs["timeout"] = 10

        if "headers" not in kwargs:
            kwargs["headers"] = self.headers.copy()
        else:
            kwargs["headers"].update(self.headers)

        # Добавление куков в заголовки
        cookies = await self.get_cookies()
        if cookies:
            cookie_header = "; ".join([f"{key}={value}" for key, value in cookies.items()])
            kwargs["headers"]["Cookie"] = cookie_header

        return kwargs

    async def request(self, method: str, url: str, **kwargs):
        await self.open_session()
        kwargs = await self.fetch_kwargs(**kwargs)
        data = {
            "method": method.upper(),
            "url": url,
            "headers": kwargs.get("headers", {}),
            "proxy": kwargs.get("proxy", ""),
            "params": kwargs.get("params", {}),
            "body": kwargs.get("json", {}),
            "content_type": "application/json"
        }

        async with self.session.post(self.server_url, json=data) as response:
            
            if response.status == 200:
                return await response.json()
            else:
                raise BadStatusCode(
                    f'[{url}:{method.upper()}] returned bad response code: {response.status} | {await response.text()}'
                )

    async def request_without_response(self, method: str, url: str, **kwargs):
        await self.open_session()
        kwargs = await self.fetch_kwargs(**kwargs)
        data = {
            "method": method.upper(),
            "url": url,
            "headers": kwargs.get("headers", {}),
            "proxy": kwargs.get("proxy", ""),
            "params": kwargs.get("params", {}),
            "body": kwargs.get("json", {}),
            "content_type": "application/json"
        }

        async with self.session.post(self.server_url, json=data) as response:
            pass
