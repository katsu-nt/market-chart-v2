from fastapi import APIRouter, Query, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, timedelta, datetime
from typing import Optional, List, Dict, Any
import json

from app.database import get_db
from app.models.exchange import (
    Currency, CentralExchangeRate, MarketExchangeRate,
    FinancialIndexMeta, FinancialIndexValue
)

router = APIRouter(prefix="/api/exchange", tags=["Exchange"])

# ======== GET ROUTES ========

@router.get("/crr")
def get_current(
    type: str = Query(..., description="'central' (tỷ giá trung tâm), 'market' (tỷ giá thị trường), 'index' (chỉ số tài chính)"),
    code: str = Query(..., description="Mã tiền tệ hoặc mã chỉ số, VD: USD, DXY"),
    db: Session = Depends(get_db)
):
    """
    Lấy giá trị mới nhất cho một currency hoặc chỉ số, kèm phần trăm chênh lệch so với lần gần nhất trước đó (delta_percent).
    """
    if type == "central":
        cur = db.query(Currency).filter_by(code=code).first()
        if not cur:
            return {"status": "error", "message": "Không tìm thấy currency"}
        latest = (
            db.query(CentralExchangeRate)
            .filter(CentralExchangeRate.currency_id == cur.id)
            .order_by(CentralExchangeRate.date.desc())
            .first()
        )
        if not latest:
            return {"status": "error", "message": f"Không có tỷ giá trung tâm cho {code}"}
        prev = (
            db.query(CentralExchangeRate)
            .filter(
                CentralExchangeRate.currency_id == cur.id,
                CentralExchangeRate.date < latest.date
            )
            .order_by(CentralExchangeRate.date.desc())
            .first()
        )
        delta_percent = (
            (float(latest.rate) - float(prev.rate)) / float(prev.rate) * 100
            if prev and prev.rate else None
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
    elif type == "market":
        cur = db.query(Currency).filter_by(code=code).first()
        if not cur:
            return {"status": "error", "message": "Không tìm thấy currency"}
        latest = (
            db.query(MarketExchangeRate)
            .filter(MarketExchangeRate.currency_id == cur.id)
            .order_by(MarketExchangeRate.timestamp.desc())
            .first()
        )
        if not latest:
            return {"status": "error", "message": f"Không có tỷ giá thị trường cho {code}"}
        prev = (
            db.query(MarketExchangeRate)
            .filter(
                MarketExchangeRate.currency_id == cur.id,
                MarketExchangeRate.timestamp < latest.timestamp
            )
            .order_by(MarketExchangeRate.timestamp.desc())
            .first()
        )
        delta_percent = (
            (float(latest.rate) - float(prev.rate)) / float(prev.rate) * 100
            if prev and prev.rate else None
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
    elif type == "index":
        idx = db.query(FinancialIndexMeta).filter_by(code=code).first()
        if not idx:
            return {"status": "error", "message": "Không tìm thấy index"}
        latest = (
            db.query(FinancialIndexValue)
            .filter(FinancialIndexValue.index_id == idx.id)
            .order_by(FinancialIndexValue.timestamp.desc())
            .first()
        )
        if not latest:
            return {"status": "error", "message": f"Không có giá trị chỉ số {code}"}
        prev = (
            db.query(FinancialIndexValue)
            .filter(
                FinancialIndexValue.index_id == idx.id,
                FinancialIndexValue.timestamp < latest.timestamp
            )
            .order_by(FinancialIndexValue.timestamp.desc())
            .first()
        )
        delta_percent = (
            (float(latest.value) - float(prev.value)) / float(prev.value) * 100
            if prev and prev.value else None
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


# -------------------------------------------------------

@router.get("/table")
def get_table(
    type: str = Query(..., description="'central', 'market', hoặc 'index'"),
    date_: Optional[date] = Query(default=date.today(), alias="date", description="Ngày cần xem (YYYY-MM-DD)"),
    code: Optional[str] = Query(None, description="Lọc riêng 1 loại currency/index nếu cần"),
    db: Session = Depends(get_db)
):
    """
    Lấy bảng dữ liệu (theo ngày, type, có thể lọc theo code), có thêm delta và delta_percent so với ngày trước đó.
    """
    data = []
    prev_date = date_ - timedelta(days=1)

    if type == "central":
        q = db.query(CentralExchangeRate)
        if code:
            cur = db.query(Currency).filter_by(code=code).first()
            if not cur:
                return {"status": "error", "message": "Không tìm thấy currency"}
            q = q.filter(CentralExchangeRate.currency_id == cur.id)
        q = q.filter(CentralExchangeRate.date == date_)
        id2code = {c.id: c.code for c in db.query(Currency).all()}

        # Lấy dữ liệu ngày trước đó để so sánh
        prev_q = db.query(CentralExchangeRate)
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

    elif type == "market":
        q = db.query(MarketExchangeRate)
        if code:
            cur = db.query(Currency).filter_by(code=code).first()
            if not cur:
                return {"status": "error", "message": "Không tìm thấy currency"}
            q = q.filter(MarketExchangeRate.currency_id == cur.id)
        q = q.filter(func.date(MarketExchangeRate.timestamp) == date_)
        id2code = {c.id: c.code for c in db.query(Currency).all()}

        # Lấy latest theo từng currency trong ngày được chọn
        latest_today = {}
        for r in q.order_by(MarketExchangeRate.timestamp.desc()).all():
            key = r.currency_id
            if key not in latest_today:
                latest_today[key] = r

        # Lấy latest theo từng currency trong ngày trước đó
        prev_q = db.query(MarketExchangeRate)
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

    elif type == "index":
        q = db.query(FinancialIndexValue)
        if code:
            idx = db.query(FinancialIndexMeta).filter_by(code=code).first()
            if not idx:
                return {"status": "error", "message": "Không tìm thấy index"}
            q = q.filter(FinancialIndexValue.index_id == idx.id)
        q = q.filter(func.date(FinancialIndexValue.timestamp) == date_)
        id2code = {i.id: i.code for i in db.query(FinancialIndexMeta).all()}

        # Lấy latest theo từng index trong ngày được chọn
        latest_today = {}
        for r in q.order_by(FinancialIndexValue.timestamp.desc()).all():
            key = r.index_id
            if key not in latest_today:
                latest_today[key] = r

        # Lấy latest theo từng index trong ngày trước đó
        prev_q = db.query(FinancialIndexValue)
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

    else:
        return {"status": "error", "message": "type phải là central, market, hoặc index"}
    return {
        "status": "success",
        "date": date_.isoformat(),
        "data": data
    }


# -------------------------------------------------------

@router.get("/chart")
def get_chart(
    type: str = Query(..., description="'central', 'market', hoặc 'index'"),
    code: List[str] = Query(..., description="1 hoặc nhiều mã tiền/chỉ số"),
    days: int = Query(30, ge=1, le=3650, description="Số ngày gần nhất"),
    db: Session = Depends(get_db)
):
    """
    Lấy lịch sử time-series (nhiều ngày) cho 1 hoặc nhiều currency/index.
    """
    results: Dict[str, List[Any]] = {}
    start_date = date.today() - timedelta(days=days-1)
    end_date = date.today() + timedelta(days=1)

    if type == "central":
        code2id = {c.code: c.id for c in db.query(Currency).filter(Currency.code.in_(code)).all()}
        for code_ in code:
            if code_ not in code2id:
                continue
            recs = (
                db.query(CentralExchangeRate)
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
    elif type == "market":
        code2id = {c.code: c.id for c in db.query(Currency).filter(Currency.code.in_(code)).all()}
        for code_ in code:
            if code_ not in code2id:
                continue
            recs = (
                db.query(MarketExchangeRate)
                .filter(
                    MarketExchangeRate.currency_id == code2id[code_],
                    MarketExchangeRate.timestamp >= start_date,
                    MarketExchangeRate.timestamp < end_date
                )
                .order_by(MarketExchangeRate.timestamp)
                .all()
            )
            # Group lấy latest theo ngày
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
    elif type == "index":
        code2id = {i.code: i.id for i in db.query(FinancialIndexMeta).filter(FinancialIndexMeta.code.in_(code)).all()}
        for code_ in code:
            if code_ not in code2id:
                continue
            recs = (
                db.query(FinancialIndexValue)
                .filter(
                    FinancialIndexValue.index_id == code2id[code_],
                    FinancialIndexValue.timestamp >= start_date,
                    FinancialIndexValue.timestamp < end_date
                )
                .order_by(FinancialIndexValue.timestamp)
                .all()
            )
            # Group lấy latest theo ngày
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

# --------- POST ROUTES ---------

@router.post("/import-central-rate")
async def import_central_rate_json(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Import danh sách tỷ giá trung tâm (dạng json):
    [
        {"currency": "USD", "rate": 25400, "date": "2025-08-01", "published_at": "2025-08-01T08:00:00"}
    ]
    """
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
            # Đảm bảo currency đã tồn tại
            code = row["currency"]
            currency = db.query(Currency).filter_by(code=code).first()
            if not currency:
                currency = Currency(code=code)
                db.add(currency)
                db.flush()
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
            db.merge(rec)
            count += 1
        except Exception as e:
            continue
    db.commit()
    return {"status": "success", "imported": count}

@router.post("/import-market-rate")
async def import_market_rate_json(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Import danh sách tỷ giá thị trường (dạng json):
    [
        {"currency": "USD", "rate": 25650, "timestamp": "2025-08-01T13:00:00", "source": "vietcombank", "type": "buy"}
    ]
    """
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
            code = row["currency"]
            currency = db.query(Currency).filter_by(code=code).first()
            if not currency:
                currency = Currency(code=code)
                db.add(currency)
                db.flush()
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
            db.merge(rec)
            count += 1
        except Exception as e:
            continue
    db.commit()
    return {"status": "success", "imported": count}

@router.post("/import-index")
async def import_index_json(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Import danh sách chỉ số tài chính (dạng json):
    [
        {"index": "DXY", "value": 105.6, "timestamp": "2025-08-01T15:00:00", "source": "investing"}
    ]
    """
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
            code = row["index"]
            idx = db.query(FinancialIndexMeta).filter_by(code=code).first()
            if not idx:
                idx = FinancialIndexMeta(code=code)
                db.add(idx)
                db.flush()
            value = float(row["value"])
            timestamp = datetime.fromisoformat(row["timestamp"])
            source = row.get("source", "imported")
            rec = FinancialIndexValue(
                index_id=idx.id,
                value=value,
                timestamp=timestamp,
                source=source
            )
            db.merge(rec)
            count += 1
        except Exception as e:
            continue
    db.commit()
    return {"status": "success", "imported": count}
