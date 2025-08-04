from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, timedelta, datetime
from typing import List, Dict, Any, Optional
from app.models.exchange import (
    Currency, CentralExchangeRate, MarketExchangeRate,
    FinancialIndexMeta, FinancialIndexValue
)
from app.repository.exchange_repo import ExchangeRepository

class ExchangeService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ExchangeRepository(db)

    def get_latest(self, type_: str, code: str):
        if type_ == "central":
            cur = self.repo.get_currency_by_code(code)
            if not cur:
                return {"status": "error", "message": "Không tìm thấy currency"}
            latest = self.repo.get_latest_central(cur.id)
            if not latest:
                return {"status": "error", "message": f"Không có tỷ giá trung tâm cho {code}"}
            prev = self.repo.get_prev_central(cur.id, latest.date)
            delta_percent = (
                (latest.rate - prev.rate) / prev.rate * 100 if prev and prev.rate else None
            )
            return {
                "status": "success",
                "data": {
                    "code": code,
                    "rate": float(latest.rate),
                    "date": latest.date.isoformat(),
                    "published_at": latest.published_at.isoformat() if latest.published_at else None,
                    "delta_percent": round(delta_percent, 5) if delta_percent is not None else None,
                    "previous_date": prev.date.isoformat() if prev else None
                }
            }
        elif type_ == "market":
            cur = self.repo.get_currency_by_code(code)
            if not cur:
                return {"status": "error", "message": "Không tìm thấy currency"}
            latest = self.repo.get_latest_market(cur.id)
            if not latest:
                return {"status": "error", "message": f"Không có tỷ giá thị trường cho {code}"}
            prev = self.repo.get_prev_market(cur.id, latest.timestamp)
            delta_percent = (
                (latest.rate - prev.rate) / prev.rate * 100 if prev and prev.rate else None
            )
            return {
                "status": "success",
                "data": {
                    "code": code,
                    "rate": float(latest.rate),
                    "timestamp": latest.timestamp.isoformat(),
                    "delta_percent": round(delta_percent, 5) if delta_percent is not None else None,
                    "previous_timestamp": prev.timestamp.isoformat() if prev else None
                }
            }
        elif type_ == "index":
            idx = self.repo.get_index_by_code(code)
            if not idx:
                return {"status": "error", "message": "Không tìm thấy index"}
            latest = self.repo.get_latest_index(idx.id)
            if not latest:
                return {"status": "error", "message": f"Không có giá trị chỉ số {code}"}
            prev = self.repo.get_prev_index(idx.id, latest.timestamp)
            delta_percent = (
                (latest.value - prev.value) / prev.value * 100 if prev and prev.value else None
            )
            return {
                "status": "success",
                "data": {
                    "code": code,
                    "value": float(latest.value),
                    "timestamp": latest.timestamp.isoformat(),
                    "delta_percent": round(delta_percent, 5) if delta_percent is not None else None,
                    "previous_timestamp": prev.timestamp.isoformat() if prev else None
                }
            }
        else:
            return {"status": "error", "message": "type phải là central, market, hoặc index"}

    def get_table(self, type_: str, date_: date, code: Optional[str]):
        data = []
        prev_date = date_ - timedelta(days=1)
        if type_ == "central":
            q = self.repo.db.query(CentralExchangeRate)
            if code:
                cur = self.repo.get_currency_by_code(code)
                if not cur:
                    return {"status": "error", "message": "Không tìm thấy currency"}
                q = q.filter(CentralExchangeRate.currency_id == cur.id)
            q = q.filter(CentralExchangeRate.date == date_)
            id2code = {c.id: c.code for c in self.repo.db.query(Currency).all()}

            prev_q = self.repo.db.query(CentralExchangeRate)
            if code:
                prev_q = prev_q.filter(CentralExchangeRate.currency_id == cur.id)
            prev_q = prev_q.filter(CentralExchangeRate.date == prev_date)
            prev_data = {r.currency_id: r for r in prev_q.all()}

            for r in q.all():
                prev = prev_data.get(r.currency_id)
                delta = delta_percent = None
                if prev and prev.rate:
                    delta = float(r.rate) - float(prev.rate)
                    delta_percent = (delta / float(prev.rate)) * 100 if prev.rate else None
                data.append({
                    "code": id2code.get(r.currency_id, "???"),
                    "rate": float(r.rate),
                    "date": r.date.isoformat(),
                    "published_at": r.published_at.isoformat() if r.published_at else None,
                    "delta": round(delta, 5) if delta is not None else None,
                    "delta_percent": round(delta_percent, 5) if delta_percent is not None else None,
                    "prev_rate": float(prev.rate) if prev else None,
                })
            return {"status": "success", "date": date_.isoformat(), "data": data}

        elif type_ == "market":
            q = self.repo.db.query(MarketExchangeRate)
            if code:
                cur = self.repo.get_currency_by_code(code)
                if not cur:
                    return {"status": "error", "message": "Không tìm thấy currency"}
                q = q.filter(MarketExchangeRate.currency_id == cur.id)
            q = q.filter(func.date(MarketExchangeRate.timestamp) == date_)
            id2code = {c.id: c.code for c in self.repo.db.query(Currency).all()}

            latest_today = {}
            for r in q.order_by(MarketExchangeRate.timestamp.desc()).all():
                key = r.currency_id
                if key not in latest_today:
                    latest_today[key] = r

            prev_q = self.repo.db.query(MarketExchangeRate)
            if code:
                prev_q = prev_q.filter(MarketExchangeRate.currency_id == cur.id)
            prev_q = prev_q.filter(func.date(MarketExchangeRate.timestamp) == prev_date)
            latest_prev = {}
            for r in prev_q.order_by(MarketExchangeRate.timestamp.desc()).all():
                key = r.currency_id
                if key not in latest_prev:
                    latest_prev[key] = r

            for cid, r in latest_today.items():
                prev = latest_prev.get(cid)
                delta = delta_percent = None
                if prev and prev.rate:
                    delta = float(r.rate) - float(prev.rate)
                    delta_percent = (delta / float(prev.rate)) * 100 if prev.rate else None
                data.append({
                    "code": id2code.get(r.currency_id, "???"),
                    "rate": float(r.rate),
                    "timestamp": r.timestamp.isoformat(),
                    "delta": round(delta, 5) if delta is not None else None,
                    "delta_percent": round(delta_percent, 5) if delta_percent is not None else None,
                    "prev_rate": float(prev.rate) if prev else None,
                })
            return {"status": "success", "date": date_.isoformat(), "data": data}

        elif type_ == "index":
            q = self.repo.db.query(FinancialIndexValue)
            if code:
                idx = self.repo.get_index_by_code(code)
                if not idx:
                    return {"status": "error", "message": "Không tìm thấy index"}
                q = q.filter(FinancialIndexValue.index_id == idx.id)
            q = q.filter(func.date(FinancialIndexValue.timestamp) == date_)
            id2code = {i.id: i.code for i in self.repo.db.query(FinancialIndexMeta).all()}

            latest_today = {}
            for r in q.order_by(FinancialIndexValue.timestamp.desc()).all():
                key = r.index_id
                if key not in latest_today:
                    latest_today[key] = r

            prev_q = self.repo.db.query(FinancialIndexValue)
            if code:
                prev_q = prev_q.filter(FinancialIndexValue.index_id == idx.id)
            prev_q = prev_q.filter(func.date(FinancialIndexValue.timestamp) == prev_date)
            latest_prev = {}
            for r in prev_q.order_by(FinancialIndexValue.timestamp.desc()).all():
                key = r.index_id
                if key not in latest_prev:
                    latest_prev[key] = r

            for iid, r in latest_today.items():
                prev = latest_prev.get(iid)
                delta = delta_percent = None
                if prev and prev.value:
                    delta = float(r.value) - float(prev.value)
                    delta_percent = (delta / float(prev.value)) * 100 if prev.value else None
                data.append({
                    "code": id2code.get(r.index_id, "???"),
                    "value": float(r.value),
                    "timestamp": r.timestamp.isoformat(),
                    "delta": round(delta, 5) if delta is not None else None,
                    "delta_percent": round(delta_percent, 5) if delta_percent is not None else None,
                    "prev_value": float(prev.value) if prev else None,
                })
            return {"status": "success", "date": date_.isoformat(), "data": data}
        else:
            return {"status": "error", "message": "type phải là central, market, hoặc index"}

    def get_chart(self, type_: str, code: List[str], days: int):
        from app.models.exchange import Currency, FinancialIndexMeta, CentralExchangeRate, MarketExchangeRate, FinancialIndexValue
        from sqlalchemy import func
        results = {}
        start_date = date.today() - timedelta(days=days-1)
        end_date = date.today() + timedelta(days=1)
        if type_ == "central":
            code2id = {c.code: c.id for c in self.repo.db.query(Currency).filter(Currency.code.in_(code)).all()}
            for code_ in code:
                if code_ not in code2id:
                    continue
                recs = (
                    self.repo.db.query(CentralExchangeRate)
                    .filter(
                        CentralExchangeRate.currency_id == code2id[code_],
                        CentralExchangeRate.date >= start_date,
                        CentralExchangeRate.date < end_date
                    )
                    .order_by(CentralExchangeRate.date)
                    .all()
                )
                results[code_] = [
                    {
                        "date": r.date.isoformat(),
                        "rate": float(r.rate),
                        "published_at": r.published_at.isoformat() if r.published_at else None
                    }
                    for r in recs
                ]
        elif type_ == "market":
            code2id = {c.code: c.id for c in self.repo.db.query(Currency).filter(Currency.code.in_(code)).all()}
            for code_ in code:
                if code_ not in code2id:
                    continue
                recs = (
                    self.repo.db.query(MarketExchangeRate)
                    .filter(
                        MarketExchangeRate.currency_id == code2id[code_],
                        MarketExchangeRate.timestamp >= start_date,
                        MarketExchangeRate.timestamp < end_date
                    )
                    .order_by(MarketExchangeRate.timestamp)
                    .all()
                )
                daily_latest = {}
                for r in recs:
                    d = r.timestamp.date()
                    if d not in daily_latest or r.timestamp > daily_latest[d].timestamp:
                        daily_latest[d] = r
                sorted_items = sorted(daily_latest.items())
                results[code_] = [
                    {
                        "date": d.isoformat(),
                        "rate": float(r.rate),
                    }
                    for d, r in sorted_items
                ]
        elif type_ == "index":
            code2id = {i.code: i.id for i in self.repo.db.query(FinancialIndexMeta).filter(FinancialIndexMeta.code.in_(code)).all()}
            for code_ in code:
                if code_ not in code2id:
                    continue
                recs = (
                    self.repo.db.query(FinancialIndexValue)
                    .filter(
                        FinancialIndexValue.index_id == code2id[code_],
                        FinancialIndexValue.timestamp >= start_date,
                        FinancialIndexValue.timestamp < end_date
                    )
                    .order_by(FinancialIndexValue.timestamp)
                    .all()
                )
                daily_latest = {}
                for r in recs:
                    d = r.timestamp.date()
                    if d not in daily_latest or r.timestamp > daily_latest[d].timestamp:
                        daily_latest[d] = r
                sorted_items = sorted(daily_latest.items())
                results[code_] = [
                    {
                        "date": d.isoformat(),
                        "value": float(r.value),
                    }
                    for d, r in sorted_items
                ]
        else:
            return {"status": "error", "message": "type phải là central, market, hoặc index"}

        return {
            "status": "success",
            "data": results
        }

    def import_central_rate(self, data: list):
        from app.models.exchange import Currency, CentralExchangeRate
        count = 0
        for row in data:
            code = row["currency"]
            currency = self.repo.db.query(Currency).filter_by(code=code).first()
            if not currency:
                currency = Currency(code=code)
                self.repo.db.add(currency)
                self.repo.db.flush()
            rate = float(row["rate"])
            date_val = date.fromisoformat(row["date"])
            published_at = (
                datetime.fromisoformat(row["published_at"]) if row.get("published_at") else None
            )
            rec = CentralExchangeRate(
                currency_id=currency.id,
                rate=rate,
                date=date_val,
                published_at=published_at
            )
            self.repo.db.merge(rec)
            count += 1
        self.repo.db.commit()
        return {"status": "success", "imported": count}

    def import_market_rate(self, data: list):
        from app.models.exchange import Currency, MarketExchangeRate
        count = 0
        for row in data:
            code = row["currency"]
            currency = self.repo.db.query(Currency).filter_by(code=code).first()
            if not currency:
                currency = Currency(code=code)
                self.repo.db.add(currency)
                self.repo.db.flush()
            rate = float(row["rate"])
            timestamp = datetime.fromisoformat(row["timestamp"])
            source = row.get("source", "imported")
            type_val = row.get("type")
            rec = MarketExchangeRate(
                currency_id=currency.id,
                rate=rate,
                timestamp=timestamp,
                source=source,
                type=type_val
            )
            self.repo.db.merge(rec)
            count += 1
        self.repo.db.commit()
        return {"status": "success", "imported": count}

    def import_index(self, data: list):
        from app.models.exchange import FinancialIndexMeta, FinancialIndexValue
        count = 0
        for row in data:
            code = row["index"]
            idx = self.repo.db.query(FinancialIndexMeta).filter_by(code=code).first()
            if not idx:
                idx = FinancialIndexMeta(code=code)
                self.repo.db.add(idx)
                self.repo.db.flush()
            value = float(row["value"])
            timestamp = datetime.fromisoformat(row["timestamp"])
            source = row.get("source", "imported")
            rec = FinancialIndexValue(
                index_id=idx.id,
                value=value,
                timestamp=timestamp,
                source=source
            )
            self.repo.db.merge(rec)
            count += 1
        self.repo.db.commit()
        return {"status": "success", "imported": count}
