from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, timedelta
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.models.gold import GoldPrice, GoldType, Location
from app.services.import_pnj_to_db import insert_gold_prices_for_date

router = APIRouter(prefix="/gold", tags=["Gold Prices"])


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

    end_date = date.today() + timedelta(days=1)  # 👈 fix: bao phủ cả ngày hiện tại
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
                    GoldPrice.timestamp < end_date  # dùng '<' để tránh lỗi timezone
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
    prices = (
        db.query(GoldPrice)
        .filter(func.date(GoldPrice.timestamp) == selected_date)
        .order_by(GoldPrice.timestamp.desc())
        .all()
    )

    latest_prices = {}
    for p in prices:
        key = (p.gold_type_id, p.unit_id, p.location_id)
        if key not in latest_prices:
            latest_prices[key] = p

    data = []
    for p in latest_prices.values():
        data.append({
            "timestamp": p.timestamp.isoformat(),
            "buy_price": float(p.buy_price),
            "sell_price": float(p.sell_price),
            "gold_type": p.gold_type.code,
            "unit": p.unit.code,
            "location": p.location.code
        })

    return {
        "status": "success",
        "message": f"Found {len(data)} records for {selected_date}",
        "data": data
    }


# -------------------------------
# ✅ POST /gold/import
# -------------------------------

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
