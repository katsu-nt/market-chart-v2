from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Currency(Base):
    __tablename__ = "currency"
    id = Column(Integer, primary_key=True)
    code = Column(String(10), unique=True, index=True, nullable=False)
    rates_central = relationship("CentralExchangeRate", back_populates="currency")
    rates_market = relationship("MarketExchangeRate", back_populates="currency")

class FinancialIndexMeta(Base):
    __tablename__ = "financial_index"
    id = Column(Integer, primary_key=True)
    code = Column(String(10), unique=True, index=True, nullable=False)
    values = relationship("FinancialIndexValue", back_populates="index")

class CentralExchangeRate(Base):
    __tablename__ = "exchange_central_rates"
    currency_id = Column(Integer, ForeignKey("currency.id"), primary_key=True, index=True)
    date = Column(Date, primary_key=True, index=True)
    rate = Column(Float, nullable=False)
    published_at = Column(DateTime, nullable=True)
    currency = relationship("Currency", back_populates="rates_central")

class MarketExchangeRate(Base):
    __tablename__ = "exchange_market_rates"
    currency_id = Column(Integer, ForeignKey("currency.id"), primary_key=True, index=True)
    timestamp = Column(DateTime, primary_key=True, index=True)
    source = Column(String, primary_key=True, index=True)
    type = Column(String, primary_key=True, nullable=True)
    rate = Column(Float, nullable=False)
    currency = relationship("Currency", back_populates="rates_market")

class FinancialIndexValue(Base):
    __tablename__ = "financial_index_values"
    index_id = Column(Integer, ForeignKey("financial_index.id"), primary_key=True, index=True)
    timestamp = Column(DateTime, primary_key=True, index=True)
    source = Column(String, primary_key=True, index=True)
    value = Column(Float, nullable=False)
    index = relationship("FinancialIndexMeta", back_populates="values")
