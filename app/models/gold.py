from sqlalchemy import Column, Integer, String, DateTime, Date, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class GoldType(Base):
    __tablename__ = "gold_types"

    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)  # ví dụ: "pnj_mieng"
    name = Column(String, nullable=False)               # mô tả: "PNJ vàng miếng"
    source = Column(String, nullable=False)             # nguồn: "pnj"

    prices = relationship("GoldPrice", back_populates="gold_type")


class Unit(Base):
    __tablename__ = "units"

    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)  # ví dụ: "tael"
    name = Column(String, nullable=False)               # ví dụ: "Chỉ"

    prices = relationship("GoldPrice", back_populates="unit")


class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)  # ví dụ: "hcm"
    name = Column(String, nullable=False)               # ví dụ: "TP Hồ Chí Minh"

    prices = relationship("GoldPrice", back_populates="location")


class GoldPrice(Base):
    __tablename__ = "gold_prices"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    date = Column(Date, nullable=False)  # để query nhanh theo ngày
    buy_price = Column(Numeric, nullable=False)
    sell_price = Column(Numeric, nullable=False)

    gold_type_id = Column(Integer, ForeignKey("gold_types.id"), nullable=False)
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)

    gold_type = relationship("GoldType", back_populates="prices")
    unit = relationship("Unit", back_populates="prices")
    location = relationship("Location", back_populates="prices")
