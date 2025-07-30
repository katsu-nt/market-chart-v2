from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.orm import relationship
from app.database import Base

class GoldType(Base):
    __tablename__ = "gold_types"

    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    source = Column(String, nullable=False)

    prices = relationship("GoldPrice", back_populates="gold_type")


class Unit(Base):
    __tablename__ = "units"

    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)

    prices = relationship("GoldPrice", back_populates="unit")


class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)

    prices = relationship("GoldPrice", back_populates="location")


class GoldPrice(Base):
    __tablename__ = "gold_prices"

    timestamp = Column(DateTime(timezone=False), nullable=False)
    buy_price = Column(Numeric, nullable=False)
    sell_price = Column(Numeric, nullable=False)

    gold_type_id = Column(Integer, ForeignKey("gold_types.id"), nullable=False)
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)

    gold_type = relationship("GoldType", back_populates="prices")
    unit = relationship("Unit", back_populates="prices")
    location = relationship("Location", back_populates="prices")

    __table_args__ = (
        PrimaryKeyConstraint("timestamp", "gold_type_id", "unit_id", "location_id", name="gold_price_pk"),
    )
