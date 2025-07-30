from sqlalchemy.orm import Session
from app.models.gold import GoldType, Unit, Location, GoldPrice
from datetime import datetime
import pytz

def insert_xau_usd_price(data: dict, db: Session):
    # Parse và chuẩn hóa timestamp theo giờ HCM (naive + rounded to seconds)
    dt = datetime.fromisoformat(data["timestamp"])
    hcm_tz = pytz.timezone("Asia/Ho_Chi_Minh")
    if dt.tzinfo is not None:
        dt = dt.astimezone(hcm_tz).replace(tzinfo=None)
    else:
        dt = pytz.utc.localize(dt).astimezone(hcm_tz).replace(tzinfo=None)
    dt = dt.replace(microsecond=0)  # 👈 làm tròn về giây

    timestamp = dt

    # Lấy hoặc tạo gold_type
    gt_data = data["gold_type"]
    gold_type = db.query(GoldType).filter_by(code=gt_data["code"]).first()
    if not gold_type:
        gold_type = GoldType(**gt_data)
        db.add(gold_type)
        db.flush()

    # Lấy hoặc tạo unit
    unit_data = data["unit"]
    unit = db.query(Unit).filter_by(code=unit_data["code"]).first()
    if not unit:
        unit = Unit(**unit_data)
        db.add(unit)
        db.flush()

    # Lấy hoặc tạo location
    loc_data = data["location"]
    location = db.query(Location).filter_by(code=loc_data["code"]).first()
    if not location:
        location = Location(**loc_data)
        db.add(location)
        db.flush()

    # Kiểm tra nếu bản ghi đã tồn tại (same second)
    exists = db.query(GoldPrice).filter_by(
        timestamp=timestamp,
        gold_type_id=gold_type.id,
        unit_id=unit.id,
        location_id=location.id
    ).first()

    if exists:
        return {"inserted": 0, "skipped": 1}

    # Thêm bản ghi mới
    gold_price = GoldPrice(
        timestamp=timestamp,
        buy_price=data["buy_price"],
        sell_price=data["sell_price"],
        gold_type_id=gold_type.id,
        unit_id=unit.id,
        location_id=location.id
    )
    db.add(gold_price)
    db.commit()

    return {"inserted": 1, "skipped": 0}
