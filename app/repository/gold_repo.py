from sqlalchemy.orm import Session
from app.models.gold import GoldPrice, GoldType, Unit, Location
from sqlalchemy import func, and_
from typing import Optional, List
from datetime import date, datetime, timedelta

class GoldPriceRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_gold_type_by_code(self, code: str) -> Optional[GoldType]:
        return self.db.query(GoldType).filter_by(code=code).first()

    def get_location_by_code(self, code: str) -> Optional[Location]:
        return self.db.query(Location).filter_by(code=code).first()

    def get_unit_by_code(self, code: str) -> Optional[Unit]:
        return self.db.query(Unit).filter_by(code=code).first()

    def get_latest(self, gold_type_id: int, location_id: int, unit_id: int) -> Optional[GoldPrice]:
        return (
            self.db.query(GoldPrice)
            .filter_by(gold_type_id=gold_type_id, location_id=location_id, unit_id=unit_id)
            .order_by(GoldPrice.timestamp.desc())
            .first()
        )

    def get_latest_of_previous_day(self, gold_type_id, location_id, unit_id, current_timestamp):
        prev_day = (current_timestamp.date() - timedelta(days=1))
        return (
            self.db.query(GoldPrice)
            .filter(
                GoldPrice.gold_type_id == gold_type_id,
                GoldPrice.location_id == location_id,
                GoldPrice.unit_id == unit_id,
                func.date(GoldPrice.timestamp) == prev_day
            )
            .order_by(GoldPrice.timestamp.desc())
            .first()
        )

    def get_range(self, gold_type_id: int, location_id: int, unit_id: int, start: date, end: date) -> List[GoldPrice]:
        q = (
            self.db.query(GoldPrice)
            .filter(
                GoldPrice.gold_type_id == gold_type_id,
                GoldPrice.location_id == location_id,
                GoldPrice.unit_id == unit_id,
                GoldPrice.timestamp >= datetime.combine(start, datetime.min.time()),
                GoldPrice.timestamp < datetime.combine(end + timedelta(days=1), datetime.min.time())
            )
            .order_by(GoldPrice.timestamp)
        )
        return q.all()

    def get_latest_group_by_key(self, target_date: date) -> List[GoldPrice]:
        prices = (
            self.db.query(GoldPrice)
            .filter(func.date(GoldPrice.timestamp) == target_date)
            .order_by(
                GoldPrice.gold_type_id,
                GoldPrice.unit_id,
                GoldPrice.location_id,
                GoldPrice.timestamp.desc()
            )
            .all()
        )
        latest = {}
        for p in prices:
            key = (p.gold_type_id, p.unit_id, p.location_id)
            if key not in latest:
                latest[key] = p
        return list(latest.values())

    def upsert_gold_price(self, timestamp, buy_price, sell_price, gold_type_id, unit_id, location_id):
        exists = self.db.query(GoldPrice).filter_by(
            timestamp=timestamp,
            gold_type_id=gold_type_id,
            unit_id=unit_id,
            location_id=location_id
        ).first()
        if exists:
            return None
        gp = GoldPrice(
            timestamp=timestamp,
            buy_price=buy_price,
            sell_price=sell_price,
            gold_type_id=gold_type_id,
            unit_id=unit_id,
            location_id=location_id
        )
        self.db.add(gp)
        self.db.commit()
        return gp

    def get_latest_before(self, gold_type_id, location_id, unit_id, before_ts):
        return (
            self.db.query(GoldPrice)
            .filter(
                GoldPrice.gold_type_id == gold_type_id,
                GoldPrice.location_id == location_id,
                GoldPrice.unit_id == unit_id,
                GoldPrice.timestamp < before_ts
            )
            .order_by(GoldPrice.timestamp.desc())
            .first()
        )

    def get_units_by_gold_type_and_location(self, gold_type_id: int, location_id: int):
        from app.models.gold import GoldPrice, Unit
        q = (
            self.db.query(Unit)
            .join(GoldPrice, GoldPrice.unit_id == Unit.id)
            .filter(
                GoldPrice.gold_type_id == gold_type_id,
                GoldPrice.location_id == location_id,
            )
            .distinct()
            .all()
        )
        return q
