from typing import Optional, Dict, List, Any
from datetime import datetime, date
from pydantic import BaseModel


class PredictionBase(BaseModel):
    company_symbol: str
    target_date: date
    predicted_return: float
    confidence_score: float
    direction: str
    model_version: str
    features_used: Optional[Dict[str, Any]] = None
    reasoning: Optional[str] = None
    similar_scenarios: Optional[List[Dict[str, Any]]] = None


class PredictionCreate(PredictionBase):
    prediction_date: datetime


class PredictionOut(PredictionBase):
    id: str
    prediction_date: datetime
    actual_return: Optional[float] = None
    prediction_accuracy: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PredictionSummary(BaseModel):
    symbol: str
    prediction_date: datetime
    target_date: date
    predicted_return: float
    confidence_score: float
    direction: str
    reasoning_summary: Optional[str] = None


class PredictionPerformance(BaseModel):
    total_predictions: int
    direction_accuracy: float
    average_accuracy: float
    by_confidence: Dict[str, Dict[str, Any]]
    period: Dict[str, str]