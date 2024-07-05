import aiosqlite
from utils.paths import DATABASE_PATH, SETTINGS_PATH, STATEMENT_PATH
import asyncio


async def add_or_update_item(data):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        item = data["item"]
        price = data["price"]
        address = data["details"]["address"]
        week_volume = data["details"]["week_volume"]
        floor = data["details"]["floor"]
        owned_delta = data["details"]["owned_delta"]
        sales_ratio_percent = data["sales_ratio_percent"]
        sellerFees = data["details"]["fees"]["sellerFees"]
        marketplaceFees = data["details"]["fees"]["marketplaceFees"]

        cursor = await db.execute("SELECT id FROM items WHERE item_name = ?", (item,))
        existing_id = await cursor.fetchone()

        if existing_id:
            item_id = existing_id[0]
            await db.execute('''
                UPDATE items
                SET price = ?, address = ?, week_volume = ?, floor = ?, owned_delta = ?, sales_ratio_percent = ?
                WHERE id = ?
            ''', (price, address, week_volume, floor, owned_delta, sales_ratio_percent, item_id))

            await db.execute('''
                UPDATE fees
                SET sellerFees = ?, marketplaceFees = ?
                WHERE item_id = ?
            ''', (sellerFees, marketplaceFees, item_id))
        else:
            await db.execute('''
                INSERT INTO items (item_name, price, address, week_volume, floor, owned_delta, sales_ratio_percent)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (item, price, address, week_volume, floor, owned_delta, sales_ratio_percent))

            cursor = await db.execute('SELECT last_insert_rowid()')
            item_id = (await cursor.fetchone())[0]

            await db.execute('''
                INSERT INTO fees (item_id, sellerFees, marketplaceFees)
                VALUES (?, ?, ?)
            ''', (item_id, sellerFees, marketplaceFees))

        await db.commit()


async def get_item_by_name(item_name: str) -> dict:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute('''
            SELECT i.id, i.item_name, i.price, i.address, i.week_volume, i.floor, i.owned_delta, i.sales_ratio_percent,
                   f.sellerFees, f.marketplaceFees
            FROM items i
            JOIN fees f ON i.id = f.item_id
            WHERE i.item_name = ?
        ''', (item_name,))
        rows = await cursor.fetchall()

        if rows:
            result = []
            for row in rows:
                data = {
                    "item": row[1],
                    "price": row[2],
                    "details": {
                        "address": row[3],
                        "fees": {
                            "sellerFees": row[8],
                            "marketplaceFees": row[9]
                        },
                        "week_volume": row[4],
                        "floor": row[5],
                        "owned_delta": row[6]
                    },
                    "sales_ratio_percent": row[7]
                }
                result.append(data)
            return result[0]
        else:
            return None


async def initialize_database():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY,
                item_name TEXT NOT NULL UNIQUE,
                price REAL NOT NULL,
                address TEXT NOT NULL,
                week_volume REAL,
                floor REAL,
                owned_delta REAL,
                sales_ratio_percent REAL
            )
        ''')

        await db.execute('''
            CREATE TABLE IF NOT EXISTS fees (
                item_id INTEGER,
                sellerFees REAL,
                marketplaceFees REAL,
                FOREIGN KEY (item_id) REFERENCES items (id)
            )
        ''')

        await db.commit()


################################### SETTINGS DB ####################################


async def initialize_settings_database():
    async with aiosqlite.connect(SETTINGS_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS proxies (
                type TEXT,
                proxy TEXT
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS collections (
                name TEXT
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS profit (
                value INTEGER
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS collections_parser (
                min_price REAL,
                max_price REAL,
                min_one_day_sellings INTEGER,
                min_one_day_volume INTEGER,
                offer_difference_percent INTEGER
            )
        ''')

        await db.commit()


async def get_settings_data_from_db():
    async with aiosqlite.connect(SETTINGS_PATH) as db:
        async with db.execute('SELECT * FROM proxies') as cursor:
            proxies = {}
            async for row in cursor:
                proxy_type, proxy = row
                proxies.setdefault(proxy_type, []).append(proxy)

        async with db.execute('SELECT name FROM collections') as cursor:
            collections = [row[0] async for row in cursor]

        async with db.execute('SELECT value FROM profit') as cursor:
            profit = await cursor.fetchone()
            profit = profit[0] if profit else None

        async with db.execute('SELECT * FROM collections_parser') as cursor:
            parser_data = await cursor.fetchone()
            parser_data = {
                "min_price": parser_data[0],
                "max_price": parser_data[1],
                "min_one_day_sellings": parser_data[2],
                "min_one_day_volume": parser_data[3],
                "offer_difference_percent": parser_data[4]
            } if parser_data else None

        return {
            "proxies": proxies,
            "collections": collections,
            "profit": profit,
            "collections_parser": parser_data
        }


async def update_settings_database(json_data: dict):
    async with aiosqlite.connect(SETTINGS_PATH) as db:
        if "proxies" in json_data.keys():
            # Удаление всех существующих записей из таблицы proxies
            await db.execute('DELETE FROM proxies')

            # Вставка новых записей
            for proxy_type, proxies in json_data["proxies"].items():
                for proxy in proxies:
                    await db.execute('''
                        INSERT INTO proxies (type, proxy)
                        VALUES (?, ?)
                    ''', (proxy_type, proxy))

        if "collections" in json_data.keys():
            # Удаление всех существующих записей из таблицы collections
            await db.execute('DELETE FROM collections')

            # Вставка новых записей
            for collection in json_data["collections"]:
                await db.execute('''
                    INSERT INTO collections (name)
                    VALUES (?)
                ''', (collection,))

        if "profit" in json_data.keys():
            # Удаление всех существующих записей из таблицы profit
            await db.execute('DELETE FROM profit')

            # Вставка новой записи
            await db.execute('''
                INSERT INTO profit (value)
                VALUES (?)
            ''', (json_data["profit"],))

        if "collections_parser" in json_data.keys():
            # Удаление всех существующих записей из таблицы collections_parser
            await db.execute('DELETE FROM collections_parser')

            # Вставка новой записи
            parser_data = json_data["collections_parser"]
            await db.execute('''
                INSERT INTO collections_parser (
                    min_price, max_price, min_one_day_sellings,
                    min_one_day_volume, offer_difference_percent
                )
                VALUES (?, ?, ?, ?, ?)
            ''', (
                parser_data["min_price"],
                parser_data["max_price"],
                parser_data["min_one_day_sellings"],
                parser_data["min_one_day_volume"],
                parser_data["offer_difference_percent"]
            ))

        await db.commit()


################## WORK STATEMENT ##################


async def change_work_statement(json_data: dict) -> None:
    async with aiosqlite.connect(STATEMENT_PATH) as db:

        async with db.execute('SELECT * FROM config') as cursor:
            row = await cursor.fetchone()
            if row:
                await db.execute('UPDATE config SET work_statement=? WHERE id=1', (json_data["work_statement"],))
            else:
                await db.execute('INSERT INTO config (work_statement) VALUES (?)', (json_data["work_statement"],))

        await db.commit()


async def get_data_from_db() -> dict:
    async with aiosqlite.connect(STATEMENT_PATH) as db:
        async with db.execute('SELECT work_statement FROM config WHERE id=1') as cursor:
            row = await cursor.fetchone()
            if row:
                return bool(row[0])
            else:
                return None


async def initialize_statement_database():
    async with aiosqlite.connect(STATEMENT_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS config (
                id INTEGER PRIMARY KEY,
                work_statement INTEGER
            )
        ''')
        await db.commit()
