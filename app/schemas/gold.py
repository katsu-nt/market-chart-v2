from pydantic import BaseModel
from datetime import datetime, date
from typing import List, Optional

class GoldTypeSchema(BaseModel):
    code: str
    name: str
    source: str

class UnitSchema(BaseModel):
    code: str
    name: str

class LocationSchema(BaseModel):
    code: str
    name: str

class GoldPriceBase(BaseModel):
    timestamp: datetime
    buy_price: float
    sell_price: float
    gold_type: str
    unit: str
    location: str

class GoldPriceResponse(GoldPriceBase):
    delta_buy: Optional[float] = None
    delta_sell: Optional[float] = None
    delta_buy_percent: Optional[float] = None
    delta_sell_percent: Optional[float] = None

class GoldChartItem(BaseModel):
    date: date
    price: float

class GoldChartSeries(BaseModel):
    key: str
    data: List[GoldChartItem]

class GoldChartResponse(BaseModel):
    status: str
    data: dict[str, List[GoldChartItem]]

class GoldPriceListResponse(BaseModel):
    status: str
    message: Optional[str] = None
    data: List[GoldPriceResponse]
