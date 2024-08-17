import redis
import json
from typing import Union, Dict, Any

class RedisManager:
    def __init__(self) -> None:
        self.pool = redis.ConnectionPool.from_url("redis://localhost:6379")
        self.default_client = redis.Redis(connection_pool=self.pool)
        self.active_pools = [self.default_client]

    async def get_new_client(self) -> redis.Redis:
        client = redis.Redis(connection_pool=self.pool)
        self.active_pools.append(client)
        return client
    
    async def close_all_clients(self) -> None:
        for client in self.active_pools: 
            await client.close()

    async def get_item_value(self, item: str) -> Union[Dict[str, Any], float, str, None]:
        value = await self.default_client.get(item)
        if value is None:
            return None

        value_str = value.decode("utf-8")   

        if "{" in value_str:
            try:
                return json.loads(value_str)
            except json.JSONDecodeError:
                pass

        try:
            return float(value_str)
        except ValueError:
            return value_str
    
    @staticmethod
    async def set_item_value(client: redis.Redis, item: str, value: Any) -> None:
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        await client.set(item, value)