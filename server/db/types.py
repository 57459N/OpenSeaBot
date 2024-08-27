import asyncio
from sqlalchemy import (
    Column, Integer, Text, ForeignKey, Enum,
    REAL, TIMESTAMP, Table, Boolean,
)
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import relationship, DeclarativeBase
import enum
import config


class Base(DeclarativeBase):
    pass


class UserStatus(enum.Enum):
    active = "active"
    inactive = "inactive"
    deactivated = "deactivated"
    banned = "banned"

    def __str__(self):
        return self.value


user_collection_association = Table(
    'user_collection_association',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('user.id', ondelete="CASCADE"), primary_key=True),
    Column('collection_id', Integer, ForeignKey('collection.id', ondelete="CASCADE"), primary_key=True)
)


class Collection(Base):
    __tablename__ = 'collection'

    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True, nullable=False)

    items = relationship("Item", back_populates="collection")
    users = relationship("User", secondary=user_collection_association, back_populates="collections")

    def __repr__(self):
        return f"<Collection(id={self.id}, name={self.name})>"


user_item_association = Table(
    'user_item_association',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('user.id'), primary_key=True),
    Column('item_id', Integer, ForeignKey('item.id'), primary_key=True)
)


class Item(Base):
    __tablename__ = 'item'

    id = Column(Integer, primary_key=True)
    collection_id = Column(Integer, ForeignKey(Collection.id, ondelete="CASCADE"), nullable=False)
    name = Column(Text, unique=True, nullable=False)
    price = Column(REAL, nullable=False)
    address = Column(Text, nullable=False)
    week_volume = Column(REAL)
    floor = Column(REAL)
    owned_delta = Column(REAL)
    sales_ratio_percent = Column(REAL)
    seller_fee = Column(REAL)
    marketplace_fee = Column(REAL)

    collection = relationship("Collection", back_populates="items")
    users = relationship("User", secondary=user_item_association, back_populates="items")

    def __repr__(self):
        return (f"<Item(id={self.id}, name={self.name}, price={self.price}, "
                f"collection_id={self.collection_id}, address={self.address})>")


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, comment="telegram id")
    balance = Column(REAL, server_default='0')
    status = Column(Enum(UserStatus), server_default=str(UserStatus.inactive))
    bot_wallet_address = Column(Text, unique=True, nullable=False)
    private_key = Column(Text, unique=True, nullable=False)

    running = relationship('IsRunning', back_populates="user", uselist=True, lazy="selectin", single_parent=True)
    parser_settings = relationship("CollectionsParserSettings", uselist=True, back_populates="user", single_parent=True)
    proxies = relationship("Proxy", back_populates="user", uselist=True)
    payments = relationship("Payment", back_populates="user")
    items = relationship("Item", secondary=user_item_association, back_populates="users")
    collections = relationship("Collection", secondary=user_collection_association, back_populates="users")

    def __repr__(self):
        return (f"<User(id={self.id}, balance={self.balance}, status={self.status}, "
                f"bot_wallet_address={self.bot_wallet_address})>")


class CollectionsParserSettings(Base):
    __tablename__ = 'collections_parser_settings'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey(User.id, ondelete="CASCADE"), unique=True)
    min_price = Column(REAL, server_default='0.1')
    max_price = Column(REAL, server_default='2')
    min_one_day_sellings = Column(Integer, server_default='10')
    min_one_day_volume = Column(Integer, server_default='5')
    offer_difference_percent = Column(REAL, server_default='2')
    profit_percent = Column(REAL, server_default='7')

    user = relationship("User", back_populates="parser_settings", single_parent=True)

    def __repr__(self):
        return (f"<CollectionsParserSettings(id={self.id}, user_id={self.user_id}, "
                f"min_price={self.min_price}, max_price={self.max_price})>")


class Proxy(Base):
    __tablename__ = 'proxy'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey(User.id, ondelete="SET NULL"))
    url = Column(Text, nullable=False)

    user = relationship("User", back_populates="proxies", single_parent=True)

    def __repr__(self):
        return f"<Proxy(id={self.id}, user_id={self.user_id}, proxy={self.proxy})>"


class Payment(Base):
    __tablename__ = 'payment'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey(User.id, ondelete="NO ACTION"), nullable=False)
    wallet_address = Column(Text, unique=True, nullable=False)
    private_key = Column(Text, unique=True, nullable=False)
    chain_id = Column(Integer, nullable=False)
    paid = Column(REAL, default=0)
    created = Column(TIMESTAMP, nullable=False)

    user = relationship("User", back_populates="payments", single_parent=True)

    def __repr__(self):
        return (f"<Payment(id={self.id}, user_id={self.user_id}, wallet_address={self.wallet_address}, "
                f"paid={self.paid}, created={self.created})>")


class IsRunning(Base):
    __tablename__ = 'is_running'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey(User.id, ondelete="CASCADE"), nullable=False, unique=True)
    bidder = Column(Boolean, server_default='false', nullable=False)
    seller = Column(Boolean, server_default='false', nullable=False)

    user = relationship('User', back_populates='running', single_parent=True)

    def __repr__(self):
        return (f"<IsRunning(id={self.id}, user_id={self.user_id}, bidder={self.bidder}, seller={self.seller})>")


async def init():
    engine = create_async_engine(
        f'{config.DB_TYPE}+{config.DB_ENGINE}://{config.DB_USER}:{config.DB_PASSWORD}@{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}')
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.commit()


if __name__ == '__main__':
    asyncio.run(init())
