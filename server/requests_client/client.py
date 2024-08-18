import aiohttp
from requests_client.utils.exceptions import BadStatusCode
from requests_client.utils.headers import DEFAULT_HEADERS
import random


class RequestsClient:
    def __init__(self, proxy: list = [], headers: dict = DEFAULT_HEADERS) -> None:
        self.proxies = proxy
        self.session = None
        self.headers = headers

    async def close_session(self) -> None:
        if self.session:
            await self.session.close()
            self.session = None

    async def open_session(self) -> None:
        if not self.session:
            self.session = aiohttp.ClientSession(trust_env=True)

    async def get_cookies(self) -> dict:
        if self.session:
            cookies_dict = {cookie.key: cookie.value for cookie in self.session.cookie_jar}
            return cookies_dict
        return {}

    async def request(self, method: str, url: str, **kwargs) -> dict:
        if not kwargs.get("proxy"):
            kwargs["proxy"] = random.choice(self.proxies)

        if not kwargs.get("timeout"):
            kwargs["timeout"] = 1

        if "headers" in kwargs.keys():
            if type(kwargs["headers"]) is dict:
                kwargs["headers"].update(self.headers)
        else:
            kwargs["headers"] = self.headers
        
        await self.open_session()

        async with self.session.request(
                method.upper(),
                url,
                ssl=False,
                **kwargs
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise BadStatusCode(
                    f'[{url}:{method.upper()}] return bad response code: {response.status}\nText: {await response.text()}'
                )

    async def request_without_response(self, method: str, url: str, **kwargs) -> dict:
        if not kwargs.get("proxy"):
            kwargs["proxy"] = random.choice(self.proxies)

        if "headers" in kwargs.keys():
            if type(kwargs["headers"]) is dict:
                kwargs["headers"].update(self.headers)
        else:
            kwargs["headers"] = self.headers

        await self.open_session()
        await self.session.request(method.upper(), url, ssl=False, **kwargs)
