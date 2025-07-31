# app/models/exchange.py

from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Currency(Base):
    """
    Model lưu thông tin loại tiền tệ (ISO).
    """
    __tablename__ = "currency"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(3), unique=True, nullable=False, index=True)   
    name = Column(String, nullable=False)                             
    symbol = Column(String)                                             
    country = Column(String)                                            

    def __repr__(self):
        return f"<Currency(code={self.code}, name={self.name})>"

class ExchangeRate(Base):
    """
    Model lưu tỷ giá đối hoái giữa hai loại tiền tệ tại một thời điểm, một nguồn nhất định.
    Khóa chính: (base_currency_id, quote_currency_id, timestamp, source)
    """
    __tablename__ = "exchange_rate"

    base_currency_id = Column(Integer, ForeignKey("currency.id"), primary_key=True)
    quote_currency_id = Column(Integer, ForeignKey("currency.id"), primary_key=True)
    timestamp = Column(DateTime(timezone=False), primary_key=True, index=True)
    source = Column(String, primary_key=True)

    rate = Column(Float, nullable=False)

    base_currency = relationship("Currency", foreign_keys=[base_currency_id])
    quote_currency = relationship("Currency", foreign_keys=[quote_currency_id])

    def __repr__(self):
        return (f"<ExchangeRate({self.base_currency_id}/{self.quote_currency_id} "
                f"rate={self.rate} source={self.source} timestamp={self.timestamp})>")

class DXYIndex(Base):
    """
    Model lưu giá trị chỉ số DXY (US Dollar Index) theo thời gian.
    Khóa chính: (timestamp, source)
    """
    __tablename__ = "dxy_index"

    timestamp = Column(DateTime(timezone=False), primary_key=True, index=True)
    source = Column(String, primary_key=True)
    value = Column(Float, nullable=False)

    def __repr__(self):
        return f"<DXYIndex(timestamp={self.timestamp}, value={self.value}, source={self.source})>"
