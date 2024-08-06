import pathlib
import sqlite3


class DataBase:
    def __init__(self):
        self.path = pathlib.Path(__file__).parent / "data" / "temporary_wallets.db"
        self.connection = sqlite3.connect(self.path)
        self._create_table()

    def _create_table(self):
        c = self.connection
        c.execute("create table if not exists temporary_wallets"
                  "("
                  "uid INTEGER, "
                  "address TEXT not null, "
                  "private_key TEXT not null, "
                  "chain_id INTEGER not null default -1, "
                  "paid INTEGER not null default 0, "
                  "PRIMARY KEY (uid, address)"
                  ");")
        c.execute("create unique index if not exists user_wallet_index "
                  "on temporary_wallets (uid, address)")
        c.commit()

    def insert(self, uid: str | int, address: str, private_key: str, chain_id: int = -1, paid: int = 0):
        self.connection.execute('''
            INSERT INTO temporary_wallets (uid, address, private_key, chain_id, paid)
            VALUES (?, ?, ?, ?, ?)
        ''', (uid, address, private_key, chain_id, paid))
        self.connection.commit()

    def set_paid(self, address: str, chain_id: int, paid: int):
        self.connection.execute('''
            UPDATE temporary_wallets
            SET chain_id = ?, paid = ?  
            WHERE address = ?
        ''', (chain_id, paid, address))
        self.connection.commit()

    def __del__(self):
        if con := self.connection:
            con.close()
