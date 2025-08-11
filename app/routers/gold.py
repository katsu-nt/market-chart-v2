from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.schemas.gold import GoldPriceListResponse, GoldChartResponse
from app.services.gold_service import GoldPriceService
from app.repository.gold_repo import GoldPriceRepository
from app.database import get_db
from typing import List
from datetime import date

router = APIRouter(prefix="/api/v1/gold", tags=["Gold"])

def get_service(db: Session = Depends(get_db)):
    repo = GoldPriceRepository(db)
    return GoldPriceService(repo)

@router.get("/current", response_model=GoldPriceListResponse)
def get_current_gold_price(
    gold_type: str = Query(...),
    location: str = Query(...),
    unit: str = Query("tael"),
    service: GoldPriceService = Depends(get_service),
):
    try:
        return service.get_current_gold_price(gold_type, location, unit)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/chart", response_model=GoldChartResponse)
def get_gold_chart(
    gold_types: List[str] = Query(["sjc"]),
    locations: List[str] = Query(["hcm"]),
    days: int = Query(30, ge=1, le=3650),
    service: GoldPriceService = Depends(get_service),
):
    return service.get_gold_chart(gold_types, locations, days)

@router.get("/table", response_model=GoldPriceListResponse)
def get_gold_table(
    selected_date: date = Query(date.today()),
    service: GoldPriceService = Depends(get_service),
):
    return service.get_gold_table(selected_date)
