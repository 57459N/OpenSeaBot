import pathlib
import sqlite3


class DataBase:
    def __init__(self):
        self.path = pathlib.Path(__file__).parent / "data" / "temporary_wallets.db"
        self.connection = sqlite3.connect(self.path)

    def _create_table(self):
        c = self.connection
        c.execute("create table if not exists temporary_wallets"
                  "("
                  "uid INTEGER, "
                  "address TEXT not null, "
                  "private_key TEXT not null, "
                  "paid INTEGER not null, "
                  "PRIMARY KEY (uid, address)"
                  ");")

        c.execute("create unique index if not exists user_wallet_index "
                  "on temporary_wallets (uid, address)")
        c.commit()

    def insert(self, uid: str | int, address: str, private_key: str, paid: int):
        self.connection.execute('''
            INSERT INTO temporary_wallets (uid, address, private_key, paid)
            VALUES (?, ?, ?, ?)
        ''', (uid, address, private_key, int(paid)))
        self.connection.commit()

    def set_paid(self, address: str, paid: int):
        self.connection.execute('''
            UPDATE temporary_wallets
            SET paid = ?
            WHERE address = ?
        ''', (int(paid), address))
        self.connection.commit()

    def __del__(self):
        if con := self.connection:
            con.close()
