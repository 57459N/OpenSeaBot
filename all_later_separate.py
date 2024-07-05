import os
import shutil


async def get_proxies():
    return ['proxy1', 'proxy2', 'proxy3']


async def get_private_key(uid: int) -> str:
    return "TODO: KEY"


async def encrypt_private_key(private_key: str, password: str) -> str:
    return f"TODO: ENCRYPT KEY: {private_key}"


async def create_unit(uid: int, private_key: str, proxies: list[str]) -> bool:
    try:
        shutil.copytree('./template', f'./units/{uid}')
    except Exception as e:
        print(f'Error with COPY TEMPLATE while creating unit for user {uid}')
        print(e)
        return False

    try:
        with open(f'./units/{uid}/proxies.txt', 'w') as f:
            f.write('\n'.join(proxies))

        with open(f'./units/{uid}/data/private_key.txt', 'w') as f:
            encrypted = await encrypt_private_key(private_key, '8F9eDf6b37Db00Bcc85A31FeD8768303ac4b7400')
            f.write(encrypted)
    except Exception as e:
        print(f'Error with CONFIG FILES while creating unit for user {uid}')
        print(e)
        return False

    return True
