from app.database import SessionLocal
from app.models.gold import GoldPrice, GoldType, Location, Unit
from app.scrapers.pnj_api_scraper import fetch_pnj_history
from datetime import datetime
from app.utils.logger import get_logger

logger = get_logger(__name__)


def get_or_create(session, model, code: str, name: str):
    instance = session.query(model).filter_by(code=code).first()
    if instance:
        return instance
    instance = model(code=code, name=name)
    if model == GoldType:
        instance.source = "pnj"
    session.add(instance)
    session.commit()
    return instance

def insert_gold_prices_for_date(date_str: str):
    session = SessionLocal()
    try:
        records = fetch_pnj_history(date_str)
        count = 0

        for item in records:
            gt = get_or_create(session, GoldType, item["gold_type"], item["gold_type"])
            loc = get_or_create(session, Location, item["location"], item["location"])
            unit = get_or_create(session, Unit, item["unit"], item["unit"])

            exists = session.query(GoldPrice).filter_by(
                timestamp=item["timestamp"],
                gold_type_id=gt.id,
                unit_id=unit.id,
                location_id=loc.id
            ).first()

            if exists:
                continue  # tránh trùng lặp

            price = GoldPrice(
                timestamp=datetime.fromisoformat(item["timestamp"]),
                date=datetime.fromisoformat(item["date"]).date(),
                buy_price=item["buy_price"],
                sell_price=item["sell_price"],
                gold_type_id=gt.id,
                unit_id=unit.id,
                location_id=loc.id
            )
            session.add(price)
            count += 1

        session.commit()
        logger.info(f"✅ Inserted {count} new records for {date_str}")
    finally:
        session.close()
