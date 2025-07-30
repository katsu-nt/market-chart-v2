from app.database import SessionLocal
from app.models.gold import GoldPrice, GoldType, Location, Unit
from app.scrapers.pnj_api_scraper import fetch_pnj_history
from app.utils.logger import get_logger
from datetime import datetime

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
        inserted = 0
        skipped = 0

        for item in records:
            # Dùng tên gốc cho name, dùng normalize cho code
            gt = get_or_create(session, GoldType, item["gold_type_code"], item["gold_type_name"])
            loc = get_or_create(session, Location, item["location_code"], item["location_code"])
            unit = get_or_create(session, Unit, item["unit_code"], item["unit_code"])

            # Check composite key: timestamp + gold_type + unit + location
            exists = session.query(GoldPrice).filter_by(
                timestamp=item["timestamp"],
                gold_type_id=gt.id,
                unit_id=unit.id,
                location_id=loc.id
            ).first()

            if exists:
                skipped += 1
                continue

            price = GoldPrice(
                timestamp=item["timestamp"],
                buy_price=item["buy_price"],
                sell_price=item["sell_price"],
                gold_type_id=gt.id,
                unit_id=unit.id,
                location_id=loc.id
            )
            session.add(price)
            inserted += 1

        session.commit()
        logger.info(f"✅ Inserted {inserted} new records, ⏭️ Skipped {skipped} duplicates for {date_str}")
        return {"inserted": inserted, "skipped": skipped}

    except Exception as e:
        session.rollback()
        logger.error(f"❌ Failed to insert records for {date_str}: {e}")
        raise e

    finally:
        session.close()
