from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Double, Text, SmallInteger, BigInteger
from typing import Optional

class Base(DeclarativeBase):
    pass

class ItemMetadata(Base):
    __tablename__ = "item_metadata"

    name: Mapped[str] = mapped_column(Text, primary_key=True)
    id: Mapped[str] = mapped_column(Text, unique=True)
    min_float: Mapped[float] = mapped_column(Double)
    max_float: Mapped[float] = mapped_column(Double)
    rarity: Mapped[str] = mapped_column(Text)
    weapon: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    stattrack: Mapped[bool] = mapped_column(SmallInteger)    
    crates: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    collections: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self):
        return f"<ItemMetadata(name={self.name!r}, weapon={self.weapon!r}, rarity={self.rarity!r})>"
      
      

class ItemMarketData(Base):
    __tablename__ = "item_market_data"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text)
    hash_name: Mapped[str] = mapped_column(Text, index=True)
    sell_listings: Mapped[int] = mapped_column(BigInteger)
    sell_price: Mapped[int] = mapped_column(BigInteger)
    sell_price_text: Mapped[str] = mapped_column(Text)
    sale_price_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    app_name: Mapped[str] = mapped_column(Text)
    app_icon: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    asset_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self):
        return f"<ItemMarketData(hash_name={self.hash_name!r}, sell_price={self.sell_price!r}, listings={self.sell_listings!r})>"
      
class ItemCrateMapping(Base):
    __tablename__ = "item_crate_mapping"

    name: Mapped[str] = mapped_column(Text, primary_key=True)
    crates: Mapped[str] = mapped_column(Text, primary_key=True)

    def __repr__(self):
        return f"<ItemCrateMapping(name={self.name!r}, crate={self.crates!r})>"