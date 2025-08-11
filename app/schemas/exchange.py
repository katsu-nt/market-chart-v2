from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, List, Dict

class CentralRateItem(BaseModel):
    code: str
    rate: float
    date: date
    published_at: Optional[datetime] = None
    delta_percent: Optional[float] = None
    previous_date: Optional[date] = None

class MarketRateItem(BaseModel):
    code: str
    rate: float
    timestamp: datetime
    delta_percent: Optional[float] = None
    previous_timestamp: Optional[datetime] = None

class FinancialIndexItem(BaseModel):
    code: str
    value: float
    timestamp: datetime
    delta_percent: Optional[float] = None
    previous_timestamp: Optional[datetime] = None

class CentralRateTableItem(CentralRateItem):
    prev_rate: Optional[float] = None
    delta: Optional[float] = None

class MarketRateTableItem(MarketRateItem):
    prev_rate: Optional[float] = None
    delta: Optional[float] = None

class FinancialIndexTableItem(FinancialIndexItem):
    prev_value: Optional[float] = None
    delta: Optional[float] = None

class TableResponse(BaseModel):
    status: str
    date: date
    data: List  # hoặc Union[List[CentralRateTableItem], List[MarketRateTableItem], List[FinancialIndexTableItem]]

class ChartSeriesItem(BaseModel):
    date: date
    rate: Optional[float] = None
    value: Optional[float] = None

class ChartResponse(BaseModel):
    status: str
    data: Dict[str, List[ChartSeriesItem]]
