from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

# --- Danh mục ngoại tệ ---
class Currency(Base):
    """
    Bảng danh mục các loại tiền tệ (USD, EUR,...)
    """
    __tablename__ = "currency"
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), unique=True, index=True, nullable=False)

    def __repr__(self):
        return f"<Currency(code={self.code})>"

# --- Danh mục chỉ số tài chính ---
class FinancialIndexMeta(Base):
    """
    Bảng danh mục các chỉ số tài chính (DXY, EXY,...)
    """
    __tablename__ = "financial_index"
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), unique=True, index=True, nullable=False)

    def __repr__(self):
        return f"<FinancialIndexMeta(code={self.code})>"

# --- Tỷ giá trung tâm ---
class CentralExchangeRate(Base):
    """
    Bảng tỷ giá trung tâm do NHNN công bố
    PK: (currency_id, date)
    """
    __tablename__ = "exchange_central_rates"
    currency_id = Column(Integer, ForeignKey("currency.id"), primary_key=True, index=True)
    date = Column(Date, primary_key=True, index=True)
    rate = Column(Float, nullable=False)
    published_at = Column(DateTime, nullable=True)

    currency = relationship("Currency")

    def __repr__(self):
        return f"<CentralExchangeRate(currency_id={self.currency_id}, rate={self.rate}, date={self.date})>"

# --- Tỷ giá thị trường ---
class MarketExchangeRate(Base):
    """
    Bảng tỷ giá thị trường (ngân hàng, chợ đen...)
    PK: (currency_id, timestamp, source, type)
    """
    __tablename__ = "exchange_market_rates"
    currency_id = Column(Integer, ForeignKey("currency.id"), primary_key=True, index=True)
    timestamp = Column(DateTime, primary_key=True, index=True)  # Không timezone
    source = Column(String, primary_key=True, index=True)
    type = Column(String, primary_key=True, nullable=True)    # 'buy', 'sell',...

    rate = Column(Float, nullable=False)

    currency = relationship("Currency")

    def __repr__(self):
        return (f"<MarketExchangeRate(currency_id={self.currency_id}, type={self.type}, "
                f"rate={self.rate}, timestamp={self.timestamp}, source={self.source})>")

# --- Giá trị các chỉ số tài chính ---
class FinancialIndexValue(Base):
    """
    Bảng giá trị các chỉ số tài chính (DXY, EXY...)
    PK: (index_id, timestamp, source)
    """
    __tablename__ = "financial_index_values"
    index_id = Column(Integer, ForeignKey("financial_index.id"), primary_key=True, index=True)
    timestamp = Column(DateTime, primary_key=True, index=True)  # Không timezone
    source = Column(String, primary_key=True, index=True)

    value = Column(Float, nullable=False)

    index = relationship("FinancialIndexMeta")

    def __repr__(self):
        return (f"<FinancialIndexValue(index_id={self.index_id}, value={self.value}, "
                f"timestamp={self.timestamp}, source={self.source})>")
