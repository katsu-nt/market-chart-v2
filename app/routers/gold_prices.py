from fastapi import APIRouter, Query, Depends, File, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, timedelta, datetime
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import json

from app.database import get_db
from app.models.gold import GoldPrice, GoldType, Location, Unit
from app.services.import_pnj_to_db import insert_gold_prices_for_date

router = APIRouter(prefix="/api/gold", tags=["Gold Prices"])


@router.get("/chart")
def get_gold_chart(
    gold_types: Optional[list[str]] = Query(None, description="Mã loại vàng, ví dụ: sjc, pnj_nhan"),
    locations: Optional[list[str]] = Query(None, description="Mã địa điểm, ví dụ: hcm, hn"),
    days: int = Query(30, ge=1, le=3650, description="Số ngày gần nhất cần lấy (tối đa 10 năm)"),
    db: Session = Depends(get_db)
):
    if not gold_types:
        gold_types = ["sjc"]
    if not locations:
        locations = ["hcm"]

    end_date = date.today() + timedelta(days=1)
    start_date = end_date - timedelta(days=days)

    results = {}

    for gt_code in gold_types:
        gold_type = db.query(GoldType).filter_by(code=gt_code).first()
        if not gold_type:
            return JSONResponse(status_code=400, content={
                "status": "error",
                "message": f"Gold type '{gt_code}' not found",
                "data": None
            })

        for loc_code in locations:
            location = db.query(Location).filter_by(code=loc_code).first()
            if not location:
                return JSONResponse(status_code=400, content={
                    "status": "error",
                    "message": f"Location '{loc_code}' not found",
                    "data": None
                })

            prices = (
                db.query(GoldPrice)
                .filter(
                    GoldPrice.gold_type_id == gold_type.id,
                    GoldPrice.location_id == location.id,
                    GoldPrice.timestamp >= start_date,
                    GoldPrice.timestamp < end_date
                )
                .order_by(GoldPrice.timestamp)
                .all()
            )

            daily_latest = {}
            for p in prices:
                d = p.timestamp.date()
                if d not in daily_latest or p.timestamp > daily_latest[d].timestamp:
                    daily_latest[d] = p

            sorted_items = sorted(daily_latest.items())
            key = f"{gt_code}-{loc_code}"
            results[key] = [
                {"date": d.isoformat(), "price": float(p.sell_price)}
                for d, p in sorted_items
            ]

    return {
        "status": "success",
        "message": "Chart data fetched successfully",
        "data": results
    }


@router.get("/table")
def get_gold_table(
    selected_date: date = Query(default=date.today(), description="Ngày cần xem dữ liệu"),
    db: Session = Depends(get_db)
):
    def get_latest_by_group(target_date: date):
        prices = (
            db.query(GoldPrice)
            .filter(func.date(GoldPrice.timestamp) == target_date)
            .order_by(GoldPrice.timestamp.desc())
            .all()
        )
        latest = {}
        for p in prices:
            key = (p.gold_type_id, p.unit_id, p.location_id)
            if key not in latest:
                latest[key] = p
        return latest

    current_data = get_latest_by_group(selected_date)
    previous_data = get_latest_by_group(selected_date - timedelta(days=1))

    data = []
    for key, current in current_data.items():
        prev = previous_data.get(key)
        delta_buy = delta_sell = None

        if prev:
            delta_buy = current.buy_price - prev.buy_price
            delta_sell = current.sell_price - prev.sell_price

        data.append({
            "timestamp": current.timestamp.isoformat(),
            "buy_price": float(current.buy_price),
            "sell_price": float(current.sell_price),
            "gold_type": current.gold_type.code,
            "unit": current.unit.code,
            "location": current.location.code,
            "delta_buy": float(delta_buy) if delta_buy is not None else None,
            "delta_sell": float(delta_sell) if delta_sell is not None else None,
        })

    return {
        "status": "success",
        "message": f"Found {len(data)} records for {selected_date}",
        "data": data
    }

@router.get("/current")
def get_current_gold_price(
    gold_type: str = Query(..., description="Mã loại vàng, ví dụ: sjc"),
    location: str = Query(..., description="Mã khu vực, ví dụ: hcm"),
    db: Session = Depends(get_db)
):
    gold = db.query(GoldType).filter_by(code=gold_type).first()
    if not gold:
        return JSONResponse(status_code=400, content={
            "status": "error",
            "message": f"Gold type '{gold_type}' not found"
        })

    loc = db.query(Location).filter_by(code=location).first()
    if not loc:
        return JSONResponse(status_code=400, content={
            "status": "error",
            "message": f"Location '{location}' not found"
        })

    # Tìm ngày gần nhất có dữ liệu, tối đa 30 ngày trước hôm nay
    for day_offset in range(0, 30):
        day = date.today() - timedelta(days=day_offset)
        latest_today = (
            db.query(GoldPrice)
            .filter(
                GoldPrice.gold_type_id == gold.id,
                GoldPrice.location_id == loc.id,
                func.date(GoldPrice.timestamp) == day
            )
            .order_by(GoldPrice.timestamp.desc())
            .first()
        )
        if latest_today:
            break
    else:
        return {
            "status": "success",
            "message": "No recent data found within 30 days",
            "data": None
        }

    # Tìm dữ liệu cũ hơn trong vòng 7 ngày trước ngày tìm được ở trên
    for day_offset in range(1, 8):
        previous_day = day - timedelta(days=day_offset)
        latest_previous = (
            db.query(GoldPrice)
            .filter(
                GoldPrice.gold_type_id == gold.id,
                GoldPrice.location_id == loc.id,
                func.date(GoldPrice.timestamp) == previous_day
            )
            .order_by(GoldPrice.timestamp.desc())
            .first()
        )
        if latest_previous:
            break
    else:
        latest_previous = None

    delta_percent = None
    if latest_previous:
        try:
            delta_percent = (
                (latest_today.sell_price - latest_previous.sell_price)
                / latest_previous.sell_price * 100
            )
        except ZeroDivisionError:
            delta_percent = None

    return {
        "status": "success",
        "data": {
            "timestamp": latest_today.timestamp.isoformat(),
            "sell_price": float(latest_today.sell_price),
            "delta_percent": round(delta_percent, 2) if delta_percent is not None else None,
            "previous_timestamp": latest_previous.timestamp.isoformat() if latest_previous else None
        }
    }


class ImportRange(BaseModel):
    start_date: date
    end_date: date


@router.post("/import")
def import_pnj_data_range(
    payload: ImportRange,
    db: Session = Depends(get_db)
):
    start = payload.start_date
    end = payload.end_date

    if start > end:
        return JSONResponse(status_code=400, content={
            "status": "error",
            "message": "start_date must be <= end_date",
            "data": None
        })

    total_days = (end - start).days + 1
    report = []
    total_inserted = 0
    total_skipped = 0

    for n in range(total_days):
        day = start + timedelta(days=n)
        day_str = day.strftime("%Y%m%d")
        try:
            result = insert_gold_prices_for_date(day_str)
            report.append({
                "date": day_str,
                "status": "success",
                "inserted": result["inserted"],
                "skipped": result["skipped"]
            })
            total_inserted += result["inserted"]
            total_skipped += result["skipped"]
        except Exception as e:
            report.append({
                "date": day_str,
                "status": "error",
                "error": str(e)
            })

    return {
        "status": "completed",
        "message": f"Processed {total_days} day(s). Inserted: {total_inserted}, Skipped: {total_skipped}",
        "data": report
    }


@router.post("/import-json")
async def import_gold_data_from_json(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        content = await file.read()
        items = json.loads(content)
    except Exception as e:
        return JSONResponse(status_code=400, content={
            "status": "error",
            "message": f"Invalid JSON file: {str(e)}",
            "data": None
        })

    inserted, skipped = 0, 0
    for entry in items:
        try:
            gt_data = entry["gold_type"]
            unit_data = entry["unit"]
            loc_data = entry["location"]

            # Upsert gold_type
            gold_type = db.query(GoldType).filter_by(code=gt_data["code"]).first()
            if not gold_type:
                gold_type = GoldType(**gt_data)
                db.add(gold_type)
                db.flush()

            # Upsert unit
            unit = db.query(Unit).filter_by(code=unit_data["code"]).first()
            if not unit:
                unit = Unit(**unit_data)
                db.add(unit)
                db.flush()

            # Upsert location
            location = db.query(Location).filter_by(code=loc_data["code"]).first()
            if not location:
                location = Location(**loc_data)
                db.add(location)
                db.flush()

            timestamp = datetime.fromisoformat(entry["timestamp"])

            # Kiểm tra tồn tại
            exists = db.query(GoldPrice).filter_by(
                timestamp=timestamp,
                gold_type_id=gold_type.id,
                unit_id=unit.id,
                location_id=location.id
            ).first()

            if exists:
                skipped += 1
                continue

            # Thêm bản ghi mới
            gold_price = GoldPrice(
                timestamp=timestamp,
                buy_price=entry["buy_price"],
                sell_price=entry["sell_price"],
                gold_type_id=gold_type.id,
                unit_id=unit.id,
                location_id=location.id
            )
            db.add(gold_price)
            inserted += 1

        except Exception:
            skipped += 1  # optional: log lỗi chi tiết

    db.commit()
    return {
        "status": "success",
        "message": f"Inserted {inserted}, Skipped {skipped} records.",
        "data": {"inserted": inserted, "skipped": skipped}
    }


from app.scrapers.xau_usd_scraper import scrape_xau_usd_price
# from app.services.import_xau_usd import insert_xau_usd_price

@router.post("/scrape-xau")
def scrape_and_import_xau(db: Session = Depends(get_db)):
    try:
        data = scrape_xau_usd_price()
        # result = insert_xau_usd_price(data, db)
        return {
            "status": "success",
            "data": data
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={
            "status": "error",
            "message": str(e)
        })