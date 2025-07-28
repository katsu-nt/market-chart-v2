from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session
from datetime import date, timedelta
from fastapi.responses import JSONResponse
from app.database import get_db
from app.models.gold import GoldPrice, GoldType
from typing import Optional

router = APIRouter(prefix="/gold", tags=["Gold Prices"])



@router.get("/chart")
def get_gold_chart(
    gold_types: Optional[list[str]] = Query(None, description="Mã loại vàng, ví dụ: sjc, pnj_mieng"),
    days: int = Query(30, ge=1, le=3650, description="Số ngày gần nhất cần lấy (tối đa 10 năm)"),
    db: Session = Depends(get_db)
):
    if not gold_types:
        gold_types = ["sjc"]

    end_date = date.today()
    start_date = end_date - timedelta(days=days - 1)

    results = {}

    for code in gold_types:
        gold_type = db.query(GoldType).filter_by(code=code).first()
        if not gold_type:
            return JSONResponse(status_code=400, content={
                "status": "error",
                "message": f"Gold type '{code}' not found",
                "data": None
            })

        records = (
            db.query(GoldPrice)
            .filter(
                GoldPrice.gold_type_id == gold_type.id,
                GoldPrice.date >= start_date,
                GoldPrice.date <= end_date
            )
            .order_by(GoldPrice.date, GoldPrice.timestamp)
            .all()
        )

        # Lấy mỗi ngày một giá cuối cùng
        daily_latest = {}
        for p in records:
            if p.date not in daily_latest or p.timestamp > daily_latest[p.date].timestamp:
                daily_latest[p.date] = p

        sorted_items = sorted(daily_latest.items())
        if len(sorted_items) < 7:
            return JSONResponse(status_code=204, content={
                "status": "no_data",
                "message": f"Not enough data to build chart for '{code}' (found {len(sorted_items)} days)",
                "data": None
            })

        results[code] = [
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
    # Truy vấn tất cả các bản ghi trong ngày
    prices = (
        db.query(GoldPrice)
        .filter(GoldPrice.date == selected_date)
        .order_by(GoldPrice.timestamp.desc())
        .all()
    )

    # Lấy bản ghi cuối cùng trong ngày cho mỗi (gold_type, unit, location)
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
