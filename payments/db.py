import asyncio
import pathlib
from pathlib import Path

from aiosqlite import connect, Connection


class DataBase:
    def __init__(self):
        self.connection: Connection = connect(pathlib.Path(__file__).parent / "data" / "temporaries.db")
        asyncio.create_task(self._create_table())

    def get_connection(self) -> Connection:
        return self.connection

    async def _create_table(self):
        await self.connection.execute("create table if not exists temporary_wallets"
                                      "("
                                      "uid INTEGER PRIMARY KEY,"
                                      "address TEXT not null ,"
                                      "secret TEXT not null ,"
                                      "paid INTEGER not null"
                                      ")")
        await self.connection.execute("create unique index if not exists user_wallet_index "
                                      "on temporary_wallets (uid, address)")
        await self.connection.commit()

    async def insert(self, uid: str | int, address: str, secret: str, paid: bool):
        await self.connection.execute('''
            INSERT INTO temporary_wallets (uid, address, secret, paid)
            VALUES (?, ?, ?, ?)
        ''', (uid, address, secret, paid))
        await self.connection.commit()

    async def set_paid(self, uid: str | int, paid: bool):
        await self.connection.execute('''
            UPDATE temporary_wallets
            SET paid = ?
            WHERE uid = ?
        ''', (paid, uid))
        await self.connection.commit()

    def __del__(self):
        if con := self.connection:
            con.close()
