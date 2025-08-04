from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from datetime import date, datetime
from app.models.exchange import (
    Currency, CentralExchangeRate, MarketExchangeRate,
    FinancialIndexMeta, FinancialIndexValue
)

class ExchangeRepository:
    def __init__(self, db: Session):
        self.db = db

    # ----------- CURRENCY ---------
    def get_currency_by_code(self, code: str) -> Optional[Currency]:
        return self.db.query(Currency).filter_by(code=code).first()

    def get_all_currency(self) -> List[Currency]:
        return self.db.query(Currency).all()

    # ----------- CENTRAL RATE ----------
    def get_latest_central(self, currency_id: int) -> Optional[CentralExchangeRate]:
        return (
            self.db.query(CentralExchangeRate)
            .filter_by(currency_id=currency_id)
            .order_by(CentralExchangeRate.date.desc())
            .first()
        )

    def get_prev_central(self, currency_id: int, date_: date) -> Optional[CentralExchangeRate]:
        return (
            self.db.query(CentralExchangeRate)
            .filter(
                CentralExchangeRate.currency_id == currency_id,
                CentralExchangeRate.date < date_
            )
            .order_by(CentralExchangeRate.date.desc())
            .first()
        )

    def get_central_rates(self, date_: date) -> List[CentralExchangeRate]:
        return self.db.query(CentralExchangeRate).filter_by(date=date_).all()

    def get_central_rate_by_currency_and_date(self, currency_id: int, date_: date) -> Optional[CentralExchangeRate]:
        return self.db.query(CentralExchangeRate).filter_by(currency_id=currency_id, date=date_).first()

    # -------- MARKET RATE ----------
    def get_latest_market(self, currency_id: int) -> Optional[MarketExchangeRate]:
        return (
            self.db.query(MarketExchangeRate)
            .filter_by(currency_id=currency_id)
            .order_by(MarketExchangeRate.timestamp.desc())
            .first()
        )

    def get_prev_market(self, currency_id: int, timestamp: datetime) -> Optional[MarketExchangeRate]:
        return (
            self.db.query(MarketExchangeRate)
            .filter(
                MarketExchangeRate.currency_id == currency_id,
                MarketExchangeRate.timestamp < timestamp
            )
            .order_by(MarketExchangeRate.timestamp.desc())
            .first()
        )

    def get_market_rates(self, date_: date) -> List[MarketExchangeRate]:
        return (
            self.db.query(MarketExchangeRate)
            .filter(func.date(MarketExchangeRate.timestamp) == date_)
            .order_by(MarketExchangeRate.currency_id, MarketExchangeRate.timestamp.desc())
            .all()
        )

    # -------- FINANCIAL INDEX ---------
    def get_index_by_code(self, code: str) -> Optional[FinancialIndexMeta]:
        return self.db.query(FinancialIndexMeta).filter_by(code=code).first()

    def get_latest_index(self, index_id: int) -> Optional[FinancialIndexValue]:
        return (
            self.db.query(FinancialIndexValue)
            .filter_by(index_id=index_id)
            .order_by(FinancialIndexValue.timestamp.desc())
            .first()
        )

    def get_prev_index(self, index_id: int, timestamp: datetime) -> Optional[FinancialIndexValue]:
        return (
            self.db.query(FinancialIndexValue)
            .filter(
                FinancialIndexValue.index_id == index_id,
                FinancialIndexValue.timestamp < timestamp
            )
            .order_by(FinancialIndexValue.timestamp.desc())
            .first()
        )

    def get_index_values(self, date_: date) -> List[FinancialIndexValue]:
        return (
            self.db.query(FinancialIndexValue)
            .filter(func.date(FinancialIndexValue.timestamp) == date_)
            .order_by(FinancialIndexValue.index_id, FinancialIndexValue.timestamp.desc())
            .all()
        )
