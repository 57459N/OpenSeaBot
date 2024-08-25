import asyncio

from sqlalchemy import select, update, insert
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, selectinload
from sqlalchemy.dialects.postgresql import Insert

import config
from db.types import User, Item, Collection, Proxy, user_item_association, CollectionsParserSettings, \
    user_collection_association


class DatabaseConnection:
    def __init__(self):
        self.engine = create_async_engine(
            f'{config.DB_TYPE}+{config.DB_ENGINE}://{config.DB_USER}:{config.DB_PASSWORD}@{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}')

    def __def__(self):
        self.engine.dispose()

    async def add_or_update_item(self, uid: int, name: str, price: float, address: str, week_volume: float,
                                 floor: float,
                                 owned_delta: float, sales_ratio_percent: float, seller_fee: float,
                                 marketplace_fee: float):
        async with AsyncSession(self.engine) as session:
            async with session.begin():
                stmt = select(Item).where(Item.name == name)
                result = await session.execute(stmt)
                item = result.scalars().first()

                if item:
                    stmt = (
                        update(Item)
                        .where(Item.id == item.id)
                        .values(
                            price=price,
                            address=address,
                            week_volume=week_volume,
                            floor=floor,
                            owned_delta=owned_delta,
                            sales_ratio_percent=sales_ratio_percent,
                            seller_fee=seller_fee,
                            marketplace_fee=marketplace_fee
                        )
                    )
                    await session.execute(stmt)
                else:
                    new_item = Item(
                        collection_id=uid,
                        name=name,
                        price=price,
                        address=address,
                        week_volume=week_volume,
                        floor=floor,
                        owned_delta=owned_delta,
                        sales_ratio_percent=sales_ratio_percent,
                        seller_fee=seller_fee,
                        marketplace_fee=marketplace_fee
                    )
                    session.add(new_item)

            await session.commit()

    async def get_item_by_name(self, name: str) -> Item | None:
        try:
            async with AsyncSession(self.engine) as s:
                command = select(Item).where(Item.name == name)
                return (await s.scalars(command)).one()
        except NoResultFound:
            return None

    async def get_items_by_names(self, names: [str]):
        async with AsyncSession(self.engine) as s:
            command = select(Item).where(Item.name.in_(names))
            return (await s.scalars(command)).fetchall()

    async def get_user_proxies(self, uid: int):
        async with AsyncSession(self.engine) as s:
            return (await s.scalars(select(Proxy).where(Proxy.user_id == uid))).fetchall()

    async def get_user_collections(self, uid: int):
        async with AsyncSession(self.engine) as s:
            async with s.begin():
                # Query to get the user with their collections
                command = (
                    select(Collection.name)
                    .join(user_collection_association, Collection.id == user_collection_association.c.collection_id)
                    .join(User, User.id == user_collection_association.c.user_id)
                    .where(User.id == uid)
                )
                collections = set((await s.execute(command)).scalars().fetchall())
                return list(collections)

    async def get_user_collections_parser_settings(self, uid: int):
        async with AsyncSession(self.engine, expire_on_commit=False) as s:
            async with s.begin():
                command = select(CollectionsParserSettings).where(CollectionsParserSettings.user_id == uid)
                return (await s.execute(command)).fetchall()

    async def set_user_collections_parser_settings(self, uid: int, min_price: float, max_price: float,
                                                   min_one_day_sellings: int, min_one_day_volume: int,
                                                   offer_difference_percent: float, profit_percent: float):

        async with AsyncSession(self.engine) as session:
            async with session.begin():
                await session.execute(
                    Insert(CollectionsParserSettings)
                    .values(
                        user_id=uid,
                        min_price=min_price,
                        max_price=max_price,
                        min_one_day_sellings=min_one_day_sellings,
                        min_one_day_volume=min_one_day_volume,
                        offer_difference_percent=offer_difference_percent,
                        profit_percent=profit_percent
                    )
                    .on_conflict_do_update(
                        index_elements=['user_id'],
                        set_={
                            'min_price': min_price,
                            'max_price': max_price,
                            'min_one_day_sellings': min_one_day_sellings,
                            'min_one_day_volume': min_one_day_volume,
                            'offer_difference_percent': offer_difference_percent,
                            'profit_percent': profit_percent
                        }
                    ))

            await session.commit()


dbconn = DatabaseConnection()

if __name__ == "__main__":
    print(asyncio.run(dbconn.get_user_collections(1)))

