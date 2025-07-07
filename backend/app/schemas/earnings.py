from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class EarningsEventBase(BaseModel):
    company_symbol: str
    earnings_date: datetime
    quarter: str
    year: int
    actual_eps: Optional[float] = None
    expected_eps: Optional[float] = None
    surprise_percentage: Optional[float] = None
    actual_revenue: Optional[float] = None
    expected_revenue: Optional[float] = None
    revenue_surprise_percentage: Optional[float] = None


class EarningsEventOut(EarningsEventBase):
    id: str
    stock_price_before: Optional[float] = None
    stock_price_after_1d: Optional[float] = None
    stock_price_after_5d: Optional[float] = None
    return_1d: Optional[float] = None
    return_5d: Optional[float] = None
    sp500_return_1d: Optional[float] = None
    sector_return_1d: Optional[float] = None
    relative_return_1d: Optional[float] = None
    volume_before: Optional[float] = None
    volume_after: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class EarningsCalendarOut(BaseModel):
    company_symbol: str
    earnings_date: datetime
    quarter: str
    year: int
    expected_eps: Optional[float] = None
    expected_revenue: Optional[float] = None
    
    # Additional computed fields
    has_prediction: bool = False
    prediction_confidence: Optional[float] = None
    predicted_direction: Optional[str] = None
    historical_beat_rate: Optional[float] = None
    
    class Config:
        from_attributes = True