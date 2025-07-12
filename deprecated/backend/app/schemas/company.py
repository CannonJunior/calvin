from typing import Optional
from datetime import datetime
from pydantic import BaseModel, validator


class CompanyBase(BaseModel):
    symbol: str
    name: str
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap: Optional[float] = None
    description: Optional[str] = None
    sp500_constituent: bool = True
    pe_ratio: Optional[float] = None
    eps: Optional[float] = None
    revenue: Optional[float] = None

    @validator('symbol')
    def symbol_must_be_uppercase(cls, v):
        return v.upper() if v else v


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap: Optional[float] = None
    description: Optional[str] = None
    sp500_constituent: Optional[bool] = None
    pe_ratio: Optional[float] = None
    eps: Optional[float] = None
    revenue: Optional[float] = None


class CompanyOut(CompanyBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True