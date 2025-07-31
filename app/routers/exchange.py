from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.exchange import Currency, ExchangeRate, DXYIndex
from datetime import date, timedelta
from typing import Optional
from sqlalchemy import func
import json
from datetime import datetime

router = APIRouter(prefix="/api/exchange", tags=["Exchange"])


@router.get("/current")
def get_current_exchange_rate(
    base_currency: str = Query(..., description="Mã tiền gốc, vd: USD"),
    quote_currency: str = Query(..., description="Mã tiền quy đổi, vd: VND"),
    db: Session = Depends(get_db)
):
    base = db.query(Currency).filter_by(code=base_currency).first()
    quote = db.query(Currency).filter_by(code=quote_currency).first()
    if not base or not quote:
        return {"status": "error", "message": "Không tìm thấy currency"}
    # Lấy ngày gần nhất có dữ liệu (max 180 ngày), nguồn "bloomberg"
    for day_offset in range(0, 180):
        day = date.today() - timedelta(days=day_offset)
        latest_today = (
            db.query(ExchangeRate)
            .filter(
                ExchangeRate.base_currency_id == base.id,
                ExchangeRate.quote_currency_id == quote.id,
                ExchangeRate.source == "bloomberg",
                func.date(ExchangeRate.timestamp) == day
            )
            .order_by(ExchangeRate.timestamp.desc())
            .first()
        )
        if latest_today:
            break
    else:
        return {"status": "success", "message": "No recent data found", "data": None}

    # Lấy dữ liệu phiên trước (7 ngày gần nhất trước phiên vừa tìm được)
    for day_offset in range(1, 8):
        prev_day = day - timedelta(days=day_offset)
        latest_prev = (
            db.query(ExchangeRate)
            .filter(
                ExchangeRate.base_currency_id == base.id,
                ExchangeRate.quote_currency_id == quote.id,
                ExchangeRate.source == "bloomberg",
                func.date(ExchangeRate.timestamp) == prev_day
            )
            .order_by(ExchangeRate.timestamp.desc())
            .first()
        )
        if latest_prev:
            break
    else:
        latest_prev = None

    delta_percent = None
    if latest_prev:
        try:
            delta_percent = ((latest_today.rate - latest_prev.rate) / latest_prev.rate * 100)
        except ZeroDivisionError:
            delta_percent = None

    return {
        "status": "success",
        "data": {
            "timestamp": latest_today.timestamp.isoformat(),
            "rate": float(latest_today.rate),
            "delta_percent": round(delta_percent, 5) if delta_percent is not None else None,
            "previous_timestamp": latest_prev.timestamp.isoformat() if latest_prev else None
        }
    }



@router.get("/table")
def get_exchange_table(
    selected_date: date = Query(default=date.today(), description="Ngày cần xem"),
    db: Session = Depends(get_db)
):
    def get_latest_by_group(target_date: date):
        rates = (
            db.query(ExchangeRate)
            .filter(func.date(ExchangeRate.timestamp) == target_date)
            .order_by(ExchangeRate.timestamp.desc())
            .all()
        )
        latest = {}
        for r in rates:
            key = (r.base_currency_id, r.quote_currency_id, r.source)
            if key not in latest:
                latest[key] = r
        return latest

    current_data = get_latest_by_group(selected_date)
    previous_data = get_latest_by_group(selected_date - timedelta(days=1))

    # Đổi id sang code cho dễ nhìn
    id2code = {c.id: c.code for c in db.query(Currency).all()}

    data = []
    for key, current in current_data.items():
        prev = previous_data.get(key)
        delta_rate = None
        if prev:
            delta_rate = current.rate - prev.rate
        base_code, quote_code = id2code.get(current.base_currency_id), id2code.get(current.quote_currency_id)
        data.append({
            "timestamp": current.timestamp.isoformat(),
            "base_currency": base_code,
            "quote_currency": quote_code,
            "rate": float(current.rate),
            "source": current.source,
            "delta": float(delta_rate) if delta_rate is not None else None
        })

    return {
        "status": "success",
        "message": f"Found {len(data)} records for {selected_date}",
        "data": data
    }



@router.get("/chart")
def get_exchange_chart(
    base_currencies: Optional[list[str]] = Query(None, description="Mã tiền tệ gốc, vd: USD, EUR"),
    quote_currencies: Optional[list[str]] = Query(None, description="Mã tiền tệ quy đổi, vd: VND, USD"),
    days: int = Query(30, ge=1, le=3650, description="Số ngày gần nhất"),
    db: Session = Depends(get_db)
):
    # Mặc định nếu không chọn thì chỉ lấy USD/VND
    if not base_currencies:
        base_currencies = ["USD"]
    if not quote_currencies:
        quote_currencies = ["VND"]

    end_date = date.today() + timedelta(days=1)
    start_date = end_date - timedelta(days=days)
    results = {}

    # Tìm id của currency
    code2id = {c.code: c.id for c in db.query(Currency).filter(Currency.code.in_(base_currencies + quote_currencies)).all()}
    for base in base_currencies:
        for quote in quote_currencies:
            key = f"{base}-{quote}"
            if base not in code2id or quote not in code2id:
                continue
            rates = (
                db.query(ExchangeRate)
                .filter(
                    ExchangeRate.base_currency_id == code2id[base],
                    ExchangeRate.quote_currency_id == code2id[quote],
                    ExchangeRate.timestamp >= start_date,
                    ExchangeRate.timestamp < end_date,
                )
                .order_by(ExchangeRate.timestamp)
                .all()
            )
            
            daily_latest = {}
            for r in rates:
                d = r.timestamp.date()
                if d not in daily_latest or r.timestamp > daily_latest[d].timestamp:
                    daily_latest[d] = r
            sorted_items = sorted(daily_latest.items())
            results[key] = [
                {
                    "date": d.isoformat(),
                    "rate": float(r.rate),
                    "source": r.source   
                }
                for d, r in sorted_items
            ]
    return {
        "status": "success",
        "data": results
    }




@router.post("/import-dxy")
async def import_dxy_json(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if file.content_type not in ["application/json", "text/json"]:
        raise HTTPException(status_code=400, detail="File phải là JSON")
    raw = await file.read()
    try:
        data = json.loads(raw)
    except Exception:
        raise HTTPException(status_code=400, detail="JSON không hợp lệ")
    if not isinstance(data, list):
        raise HTTPException(status_code=400, detail="Dữ liệu phải là mảng")
    count = 0
    for row in data:
        try:
            timestamp = datetime.fromisoformat(row["timestamp"])
            value = float(row["value"])
            source = row.get("source", "imported")
            dxy = DXYIndex(timestamp=timestamp, value=value, source=source)
            db.merge(dxy)  # upsert theo khóa chính
            count += 1
        except Exception as e:
            continue
    db.commit()
    return {"status": "success", "imported": count}

@router.post("/import-rate")
async def import_exchange_rate_json(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if file.content_type not in ["application/json", "text/json"]:
        raise HTTPException(status_code=400, detail="File phải là JSON")
    raw = await file.read()
    try:
        data = json.loads(raw)
    except Exception:
        raise HTTPException(status_code=400, detail="JSON không hợp lệ")
    if not isinstance(data, list):
        raise HTTPException(status_code=400, detail="Dữ liệu phải là mảng")
    count = 0
    for row in data:
        try:
            # Thêm currency nếu chưa có
            for code in [row["base_currency"], row["quote_currency"]]:
                if not db.query(Currency).filter_by(code=code).first():
                    db.add(Currency(code=code, name=code, symbol=code, country=""))
            db.flush()
            base = db.query(Currency).filter_by(code=row["base_currency"]).first()
            quote = db.query(Currency).filter_by(code=row["quote_currency"]).first()
            timestamp = datetime.fromisoformat(row["timestamp"])
            rate = float(row["rate"])
            source = row.get("source", "imported")
            exrate = ExchangeRate(
                base_currency_id=base.id,
                quote_currency_id=quote.id,
                timestamp=timestamp,
                rate=rate,
                source=source,
            )
            db.merge(exrate)  # upsert theo khóa chính
            count += 1
        except Exception as e:
            continue
    db.commit()
    return {"status": "success", "imported": count}
