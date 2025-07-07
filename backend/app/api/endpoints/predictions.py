from typing import List, Optional
from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, desc

from app.db.database import get_db
from app.models.company import Prediction
from app.schemas.predictions import PredictionOut, PredictionCreate
from app.services.prediction_service import PredictionService

router = APIRouter()


@router.get("/", response_model=List[PredictionOut])
async def get_predictions(
    symbol: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    confidence_threshold: float = Query(0.0, ge=0.0, le=1.0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Get predictions with optional filtering"""
    query = db.query(Prediction)
    
    if symbol:
        query = query.filter(Prediction.company_symbol == symbol.upper())
    
    if start_date:
        query = query.filter(Prediction.target_date >= start_date)
    
    if end_date:
        query = query.filter(Prediction.target_date <= end_date)
    
    if confidence_threshold > 0:
        query = query.filter(Prediction.confidence_score >= confidence_threshold)
    
    predictions = await query.order_by(desc(Prediction.target_date)).limit(limit).all()
    return predictions


@router.get("/{symbol}/latest", response_model=PredictionOut)
async def get_latest_prediction(
    symbol: str,
    db: AsyncSession = Depends(get_db),
):
    """Get latest prediction for a symbol"""
    prediction = await (
        db.query(Prediction)
        .filter(Prediction.company_symbol == symbol.upper())
        .order_by(desc(Prediction.prediction_date))
        .first()
    )
    
    if not prediction:
        raise HTTPException(status_code=404, detail="No predictions found for symbol")
    
    return prediction


@router.post("/{symbol}/generate")
async def generate_prediction(
    symbol: str,
    target_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
):
    """Generate new prediction for a symbol"""
    if not target_date:
        # Default to next business day
        target_date = date.today() + timedelta(days=1)
    
    prediction_service = PredictionService(db)
    
    try:
        prediction = await prediction_service.generate_prediction(
            symbol=symbol.upper(),
            target_date=target_date,
        )
        return prediction
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate prediction: {str(e)}")


@router.get("/upcoming/all")
async def get_upcoming_predictions(
    days_ahead: int = Query(7, ge=1, le=30),
    confidence_threshold: float = Query(0.5, ge=0.0, le=1.0),
    db: AsyncSession = Depends(get_db),
):
    """Get all upcoming predictions for next N days"""
    end_date = date.today() + timedelta(days=days_ahead)
    
    predictions = await (
        db.query(Prediction)
        .filter(
            and_(
                Prediction.target_date >= date.today(),
                Prediction.target_date <= end_date,
                Prediction.confidence_score >= confidence_threshold,
            )
        )
        .order_by(Prediction.target_date, desc(Prediction.confidence_score))
        .all()
    )
    
    # Group by date and direction
    by_date = {}
    for pred in predictions:
        date_key = str(pred.target_date)
        if date_key not in by_date:
            by_date[date_key] = {"UP": [], "DOWN": [], "NEUTRAL": []}
        by_date[date_key][pred.direction].append({
            "symbol": pred.company_symbol,
            "predicted_return": pred.predicted_return,
            "confidence": pred.confidence_score,
            "reasoning": pred.reasoning[:200] + "..." if pred.reasoning and len(pred.reasoning) > 200 else pred.reasoning,
        })
    
    return {
        "date_range": {
            "start": str(date.today()),
            "end": str(end_date),
        },
        "total_predictions": len(predictions),
        "by_date": by_date,
    }


@router.get("/performance/summary")
async def get_prediction_performance(
    days_back: int = Query(30, ge=1, le=365),
    model_version: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get prediction performance summary"""
    start_date = date.today() - timedelta(days=days_back)
    
    query = db.query(Prediction).filter(
        and_(
            Prediction.target_date >= start_date,
            Prediction.target_date <= date.today(),
            Prediction.actual_return.isnot(None),
        )
    )
    
    if model_version:
        query = query.filter(Prediction.model_version == model_version)
    
    predictions = await query.all()
    
    if not predictions:
        return {"message": "No completed predictions found for the specified period"}
    
    # Calculate performance metrics
    total_predictions = len(predictions)
    correct_direction = sum(
        1 for p in predictions
        if (p.predicted_return > 0 and p.actual_return > 0) or
           (p.predicted_return < 0 and p.actual_return < 0) or
           (abs(p.predicted_return) < 0.01 and abs(p.actual_return) < 0.01)
    )
    
    avg_accuracy = sum(p.prediction_accuracy for p in predictions if p.prediction_accuracy) / len([p for p in predictions if p.prediction_accuracy])
    
    by_confidence = {"high": [], "medium": [], "low": []}
    for p in predictions:
        if p.confidence_score >= 0.8:
            by_confidence["high"].append(p)
        elif p.confidence_score >= 0.6:
            by_confidence["medium"].append(p)
        else:
            by_confidence["low"].append(p)
    
    return {
        "period": {
            "start": str(start_date),
            "end": str(date.today()),
            "days": days_back,
        },
        "total_predictions": total_predictions,
        "direction_accuracy": correct_direction / total_predictions if total_predictions > 0 else 0,
        "average_accuracy": avg_accuracy if predictions else 0,
        "by_confidence": {
            level: {
                "count": len(preds),
                "direction_accuracy": sum(
                    1 for p in preds
                    if (p.predicted_return > 0 and p.actual_return > 0) or
                       (p.predicted_return < 0 and p.actual_return < 0)
                ) / len(preds) if preds else 0,
            }
            for level, preds in by_confidence.items()
        },
    }