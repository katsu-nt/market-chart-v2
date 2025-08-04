from sqlalchemy.orm import Session
from app.models.gold import GoldType, Unit, Location, GoldPrice
from datetime import datetime

def insert_xau_usd_price(data: dict, db: Session):
    dt = data["timestamp"]
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt)
    # Lấy/insert các bảng liên quan
    gt_data = data["gold_type"]
    gold_type = db.query(GoldType).filter_by(code=gt_data["code"]).first()
    if not gold_type:
        gold_type = GoldType(**gt_data)
        db.add(gold_type)
        db.flush()
    unit_data = data["unit"]
    unit = db.query(Unit).filter_by(code=unit_data["code"]).first()
    if not unit:
        unit = Unit(**unit_data)
        db.add(unit)
        db.flush()
    loc_data = data["location"]
    location = db.query(Location).filter_by(code=loc_data["code"]).first()
    if not location:
        location = Location(**loc_data)
        db.add(location)
        db.flush()
    exists = db.query(GoldPrice).filter_by(
        timestamp=dt,
        gold_type_id=gold_type.id,
        unit_id=unit.id,
        location_id=location.id
    ).first()
    if exists:
        return {"inserted": 0, "skipped": 1}
    gold_price = GoldPrice(
        timestamp=dt,
        buy_price=data.get("buy_price", 0),
        sell_price=data.get("sell_price", 0),
        gold_type_id=gold_type.id,
        unit_id=unit.id,
        location_id=location.id
    )
    db.add(gold_price)
    db.commit()
    return {"inserted": 1, "skipped": 0}
