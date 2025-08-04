from fastapi import APIRouter, Depends, Query, HTTPException, File, UploadFile, Body
from sqlalchemy.orm import Session
from app.schemas.gold import (
    GoldPriceListResponse, GoldChartResponse, ImportRange
)
from app.services.gold_service import GoldPriceService
from app.repository.gold_repo import GoldPriceRepository
from app.database import get_db
from typing import List, Optional
from datetime import date
import json

router = APIRouter(prefix="/api/v1/gold", tags=["Gold"])

def get_service(db: Session = Depends(get_db)):
    repo = GoldPriceRepository(db)
    return GoldPriceService(repo)

@router.get("/current", response_model=GoldPriceListResponse)
def get_current_gold_price(
    gold_type: str = Query(...), 
    location: str = Query(...), 
    unit: str = Query("tael"),
    service: GoldPriceService = Depends(get_service)
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
    service: GoldPriceService = Depends(get_service)
):
    return service.get_gold_chart(gold_types, locations, days)

@router.get("/table", response_model=GoldPriceListResponse)
def get_gold_table(
    selected_date: date = Query(date.today()),
    service: GoldPriceService = Depends(get_service)
):
    return service.get_gold_table(selected_date)


@router.post("/import-json")
async def import_gold_data_from_json(
    file: UploadFile = File(...),
    service: GoldPriceService = Depends(get_service)
):
    try:
        content = await file.read()
        items = json.loads(content)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid JSON file")
    result = service.import_gold_data_from_json(items)
    return {"status": "success", "message": f"Inserted {result['inserted']}, Skipped {result['skipped']}", "data": result}

@router.post("/import")
def import_pnj_range(
    payload: ImportRange = Body(...),
    service: GoldPriceService = Depends(get_service)
):
    from app.scrapers.pnj_scraper import PNJScraper
    scraper = PNJScraper()
    result = service.import_pnj_range(payload.start_date, payload.end_date, scraper)
    return {"status": "completed", "message": f"Inserted {result['inserted']}, Skipped {result['skipped']}", "data": result["report"]}
