from fastapi import APIRouter, Depends, Query, HTTPException, File, UploadFile
from sqlalchemy.orm import Session
from datetime import date
from typing import List
from app.database import get_db
from app.services.exchange_service import ExchangeService
import json

router = APIRouter()

def get_service(db: Session = Depends(get_db)):
    return ExchangeService(db)

@router.get("/latest")
def get_latest(
    type: str = Query(..., description="'central', 'market', hoặc 'index'"),
    code: str = Query(..., description="Mã tiền hoặc mã chỉ số"),
    service: ExchangeService = Depends(get_service)
):
    try:
        return service.get_latest(type, code)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/table")
def get_table(
    type: str = Query(..., description="'central', 'market', hoặc 'index'"),
    date_: date = Query(date.today(), alias="date", description="Ngày cần xem (YYYY-MM-DD)"),
    code: str = Query(None, description="Lọc riêng 1 loại currency/index nếu cần"),
    service: ExchangeService = Depends(get_service)
):
    return service.get_table(type, date_, code)

@router.get("/chart")
def get_chart(
    type: str = Query(..., description="'central', 'market', hoặc 'index'"),
    code: List[str] = Query(..., description="1 hoặc nhiều mã tiền/chỉ số"),
    days: int = Query(30, ge=1, le=3650, description="Số ngày gần nhất"),
    service: ExchangeService = Depends(get_service)
):
    return service.get_chart(type, code, days)

@router.post("/import-central-rate")
async def import_central_rate_json(
    file: UploadFile = File(...),
    service: ExchangeService = Depends(get_service)
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
    return service.import_central_rate(data)

@router.post("/import-market-rate")
async def import_market_rate_json(
    file: UploadFile = File(...),
    service: ExchangeService = Depends(get_service)
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
    return service.import_market_rate(data)

@router.post("/import-index")
async def import_index_json(
    file: UploadFile = File(...),
    service: ExchangeService = Depends(get_service)
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
    return service.import_index(data)
