from typing import List, Optional
from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_

from app.db.database import get_db
from app.models.company import EarningsEvent
from app.schemas.earnings import EarningsEventOut, EarningsCalendarOut

router = APIRouter()


@router.get("/calendar", response_model=List[EarningsCalendarOut])
async def get_earnings_calendar(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    symbols: Optional[str] = Query(None, description="Comma-separated list of symbols"),
    db: AsyncSession = Depends(get_db),
):
    """Get earnings calendar for specified date range"""
    if not start_date:
        start_date = date.today()
    if not end_date:
        end_date = start_date + timedelta(days=30)
    
    query = db.query(EarningsEvent).filter(
        and_(
            EarningsEvent.earnings_date >= start_date,
            EarningsEvent.earnings_date <= end_date,
        )
    )
    
    if symbols:
        symbol_list = [s.strip().upper() for s in symbols.split(",")]
        query = query.filter(EarningsEvent.company_symbol.in_(symbol_list))
    
    earnings = await query.order_by(EarningsEvent.earnings_date).all()
    return earnings


@router.get("/{symbol}/history", response_model=List[EarningsEventOut])
async def get_earnings_history(
    symbol: str,
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get historical earnings for a company"""
    earnings = await (
        db.query(EarningsEvent)
        .filter(EarningsEvent.company_symbol == symbol.upper())
        .order_by(EarningsEvent.earnings_date.desc())
        .limit(limit)
        .all()
    )
    
    if not earnings:
        raise HTTPException(status_code=404, detail="No earnings data found for symbol")
    
    return earnings


@router.get("/{symbol}/next")
async def get_next_earnings(
    symbol: str,
    db: AsyncSession = Depends(get_db),
):
    """Get next scheduled earnings for a company"""
    next_earnings = await (
        db.query(EarningsEvent)
        .filter(
            and_(
                EarningsEvent.company_symbol == symbol.upper(),
                EarningsEvent.earnings_date >= datetime.now(),
            )
        )
        .order_by(EarningsEvent.earnings_date)
        .first()
    )
    
    if not next_earnings:
        return {"message": "No upcoming earnings found", "symbol": symbol.upper()}
    
    return next_earnings


@router.get("/{symbol}/performance")
async def get_earnings_performance(
    symbol: str,
    db: AsyncSession = Depends(get_db),
):
    """Get earnings performance statistics"""
    earnings = await (
        db.query(EarningsEvent)
        .filter(
            and_(
                EarningsEvent.company_symbol == symbol.upper(),
                EarningsEvent.actual_eps.isnot(None),
                EarningsEvent.expected_eps.isnot(None),
            )
        )
        .all()
    )
    
    if not earnings:
        raise HTTPException(status_code=404, detail="No earnings performance data found")
    
    # Calculate statistics
    total_earnings = len(earnings)
    beats = sum(1 for e in earnings if e.surprise_percentage and e.surprise_percentage > 0)
    misses = sum(1 for e in earnings if e.surprise_percentage and e.surprise_percentage < 0)
    meets = total_earnings - beats - misses
    
    positive_returns = sum(1 for e in earnings if e.return_1d and e.return_1d > 0)
    avg_return_1d = sum(e.return_1d for e in earnings if e.return_1d) / len([e for e in earnings if e.return_1d])
    
    avg_surprise = sum(e.surprise_percentage for e in earnings if e.surprise_percentage) / len([e for e in earnings if e.surprise_percentage])
    
    return {
        "symbol": symbol.upper(),
        "total_earnings_events": total_earnings,
        "beats": beats,
        "misses": misses,
        "meets": meets,
        "beat_rate": beats / total_earnings if total_earnings > 0 else 0,
        "positive_return_rate": positive_returns / len([e for e in earnings if e.return_1d]) if earnings else 0,
        "average_1d_return": avg_return_1d if earnings else 0,
        "average_surprise_percentage": avg_surprise if earnings else 0,
    }


@router.get("/upcoming/summary")
async def get_upcoming_earnings_summary(
    days_ahead: int = Query(7, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
):
    """Get summary of upcoming earnings"""
    end_date = datetime.now() + timedelta(days=days_ahead)
    
    earnings = await (
        db.query(EarningsEvent)
        .filter(
            and_(
                EarningsEvent.earnings_date >= datetime.now(),
                EarningsEvent.earnings_date <= end_date,
            )
        )
        .order_by(EarningsEvent.earnings_date)
        .all()
    )
    
    # Group by date
    by_date = {}
    for earning in earnings:
        date_key = earning.earnings_date.date()
        if date_key not in by_date:
            by_date[date_key] = []
        by_date[date_key].append(earning.company_symbol)
    
    return {
        "total_companies": len(earnings),
        "date_range": {
            "start": datetime.now().date(),
            "end": end_date.date(),
        },
        "by_date": {str(k): v for k, v in by_date.items()},
    }