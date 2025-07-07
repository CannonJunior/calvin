from typing import List, Optional
from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, func

from app.db.database import get_db
from app.models.company import Company, EarningsEvent, AnalystRating, InsiderTrading
from app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/dashboard/overview")
async def get_dashboard_overview(
    db: AsyncSession = Depends(get_db),
):
    """Get dashboard overview statistics"""
    analytics = AnalyticsService(db)
    
    # Get basic counts
    total_companies = await db.scalar(
        func.count(Company.id).where(Company.sp500_constituent == True)
    )
    
    # Upcoming earnings (next 7 days)
    upcoming_earnings = await db.scalar(
        func.count(EarningsEvent.id).where(
            and_(
                EarningsEvent.earnings_date >= datetime.now(),
                EarningsEvent.earnings_date <= datetime.now() + timedelta(days=7),
            )
        )
    )
    
    # Recent predictions performance
    recent_predictions = await analytics.get_recent_prediction_performance(days=30)
    
    # Market sentiment overview
    sentiment_overview = await analytics.get_market_sentiment_overview()
    
    return {
        "total_sp500_companies": total_companies,
        "upcoming_earnings_7d": upcoming_earnings,
        "recent_prediction_accuracy": recent_predictions.get("direction_accuracy", 0),
        "market_sentiment": sentiment_overview,
        "last_updated": datetime.now().isoformat(),
    }


@router.get("/sector-performance")
async def get_sector_performance(
    days_back: int = Query(30, ge=1, le=365),
    metric: str = Query("earnings_performance", regex="^(earnings_performance|stock_returns|prediction_accuracy)$"),
    db: AsyncSession = Depends(get_db),
):
    """Get sector performance analysis"""
    analytics = AnalyticsService(db)
    
    try:
        performance = await analytics.get_sector_performance(
            days_back=days_back,
            metric=metric,
        )
        return performance
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get sector performance: {str(e)}")


@router.get("/earnings-calendar/analysis")
async def get_earnings_calendar_analysis(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get detailed earnings calendar with predictions and historical performance"""
    if not start_date:
        start_date = date.today()
    if not end_date:
        end_date = start_date + timedelta(days=30)
    
    analytics = AnalyticsService(db)
    
    try:
        calendar_data = await analytics.get_earnings_calendar_analysis(
            start_date=start_date,
            end_date=end_date,
        )
        return calendar_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get earnings calendar analysis: {str(e)}")


@router.get("/company/{symbol}/profile")
async def get_company_analytics_profile(
    symbol: str,
    db: AsyncSession = Depends(get_db),
):
    """Get comprehensive analytics profile for a company"""
    analytics = AnalyticsService(db)
    
    try:
        profile = await analytics.get_company_profile(symbol.upper())
        return profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get company profile: {str(e)}")


@router.get("/insider-trading/analysis")
async def get_insider_trading_analysis(
    symbol: Optional[str] = None,
    days_back: int = Query(90, ge=1, le=365),
    transaction_type: Optional[str] = Query(None, regex="^(BUY|SELL)$"),
    db: AsyncSession = Depends(get_db),
):
    """Get insider trading analysis"""
    analytics = AnalyticsService(db)
    
    try:
        analysis = await analytics.get_insider_trading_analysis(
            symbol=symbol.upper() if symbol else None,
            days_back=days_back,
            transaction_type=transaction_type,
        )
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get insider trading analysis: {str(e)}")


@router.get("/analyst-accuracy/rankings")
async def get_analyst_accuracy_rankings(
    days_back: int = Query(365, ge=30, le=1095),
    min_ratings: int = Query(5, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Get analyst accuracy rankings"""
    analytics = AnalyticsService(db)
    
    try:
        rankings = await analytics.get_analyst_accuracy_rankings(
            days_back=days_back,
            min_ratings=min_ratings,
        )
        return rankings
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analyst rankings: {str(e)}")


@router.get("/market-patterns/analysis")
async def get_market_patterns_analysis(
    pattern_type: str = Query("post_earnings", regex="^(post_earnings|pre_earnings|analyst_upgrades|insider_activity)$"),
    symbol: Optional[str] = None,
    days_back: int = Query(365, ge=30, le=1095),
    db: AsyncSession = Depends(get_db),
):
    """Get market patterns analysis using AI agents"""
    analytics = AnalyticsService(db)
    
    try:
        patterns = await analytics.get_market_patterns(
            pattern_type=pattern_type,
            symbol=symbol.upper() if symbol else None,
            days_back=days_back,
        )
        return patterns
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get market patterns: {str(e)}")


@router.get("/volatility/analysis")
async def get_volatility_analysis(
    symbol: Optional[str] = None,
    days_back: int = Query(90, ge=30, le=365),
    event_type: str = Query("earnings", regex="^(earnings|analyst_ratings|insider_trading|all)$"),
    db: AsyncSession = Depends(get_db),
):
    """Get volatility analysis around specific events"""
    analytics = AnalyticsService(db)
    
    try:
        volatility = await analytics.get_volatility_analysis(
            symbol=symbol.upper() if symbol else None,
            days_back=days_back,
            event_type=event_type,
        )
        return volatility
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get volatility analysis: {str(e)}")


@router.get("/backtesting/results")
async def get_backtesting_results(
    model_version: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    confidence_threshold: float = Query(0.5, ge=0.0, le=1.0),
    db: AsyncSession = Depends(get_db),
):
    """Get backtesting results for prediction models"""
    analytics = AnalyticsService(db)
    
    try:
        results = await analytics.get_backtesting_results(
            model_version=model_version,
            start_date=start_date,
            end_date=end_date,
            confidence_threshold=confidence_threshold,
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get backtesting results: {str(e)}")