from typing import Dict, List, Any, Optional
from datetime import datetime, date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, func, desc
import numpy as np

from app.models.company import Company, EarningsEvent, AnalystRating, InsiderTrading, Prediction


class AnalyticsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_recent_prediction_performance(self, days: int = 30) -> Dict[str, Any]:
        """Get recent prediction performance metrics"""
        
        start_date = date.today() - timedelta(days=days)
        
        predictions = await self.db.query(Prediction).filter(
            and_(
                Prediction.target_date >= start_date,
                Prediction.target_date <= date.today(),
                Prediction.actual_return.isnot(None),
            )
        ).all()
        
        if not predictions:
            return {
                "total_predictions": 0,
                "direction_accuracy": 0.0,
                "average_accuracy": 0.0,
                "period_days": days,
            }
        
        # Calculate direction accuracy
        correct_direction = sum(
            1 for p in predictions
            if (p.predicted_return > 0 and p.actual_return > 0) or
               (p.predicted_return < 0 and p.actual_return < 0) or
               (abs(p.predicted_return) < 0.01 and abs(p.actual_return) < 0.01)
        )
        
        direction_accuracy = correct_direction / len(predictions)
        
        # Calculate average prediction accuracy
        avg_accuracy = np.mean([p.prediction_accuracy for p in predictions if p.prediction_accuracy])
        
        return {
            "total_predictions": len(predictions),
            "direction_accuracy": direction_accuracy,
            "average_accuracy": float(avg_accuracy) if avg_accuracy else 0.0,
            "period_days": days,
        }

    async def get_market_sentiment_overview(self) -> Dict[str, Any]:
        """Get overall market sentiment based on recent data"""
        
        # Get recent analyst ratings
        recent_ratings = await self.db.query(AnalystRating).filter(
            AnalystRating.rating_date >= date.today() - timedelta(days=30)
        ).all()
        
        if not recent_ratings:
            return {
                "overall_score": 5.0,
                "bullish_percentage": 33.3,
                "bearish_percentage": 33.3,
                "neutral_percentage": 33.4,
            }
        
        # Calculate sentiment distribution
        bullish_ratings = sum(1 for r in recent_ratings if r.rating.upper() in ['BUY', 'STRONG BUY'])
        bearish_ratings = sum(1 for r in recent_ratings if r.rating.upper() in ['SELL', 'STRONG SELL'])
        neutral_ratings = len(recent_ratings) - bullish_ratings - bearish_ratings
        
        total_ratings = len(recent_ratings)
        
        bullish_pct = (bullish_ratings / total_ratings) * 100
        bearish_pct = (bearish_ratings / total_ratings) * 100
        neutral_pct = (neutral_ratings / total_ratings) * 100
        
        # Calculate overall sentiment score (1-10 scale)
        overall_score = 5.0 + (bullish_pct - bearish_pct) / 20  # Scale to 1-10
        overall_score = max(1.0, min(10.0, overall_score))
        
        return {
            "overall_score": overall_score,
            "bullish_percentage": bullish_pct,
            "bearish_percentage": bearish_pct,
            "neutral_percentage": neutral_pct,
        }

    async def get_sector_performance(
        self, 
        days_back: int = 30, 
        metric: str = "earnings_performance"
    ) -> Dict[str, Any]:
        """Get sector performance analysis"""
        
        start_date = date.today() - timedelta(days=days_back)
        
        if metric == "earnings_performance":
            # Get earnings performance by sector
            result = await self.db.execute(f"""
                SELECT 
                    c.sector,
                    COUNT(e.id) as total_earnings,
                    AVG(CASE WHEN e.surprise_percentage > 0 THEN 1.0 ELSE 0.0 END) as beat_rate,
                    AVG(e.surprise_percentage) as avg_surprise,
                    AVG(e.return_1d) as avg_return_1d
                FROM companies c
                JOIN earnings_events e ON c.symbol = e.company_symbol
                WHERE e.earnings_date >= '{start_date}'
                    AND c.sector IS NOT NULL
                GROUP BY c.sector
                ORDER BY beat_rate DESC
            """)
            
            sectors = []
            for row in result.fetchall():
                sectors.append({
                    "sector": row[0],
                    "total_earnings": row[1],
                    "beat_rate": float(row[2]) if row[2] else 0.0,
                    "avg_surprise": float(row[3]) if row[3] else 0.0,
                    "avg_return_1d": float(row[4]) if row[4] else 0.0,
                })
            
            return {
                "metric": metric,
                "period_days": days_back,
                "sectors": sectors,
                "timestamp": datetime.now().isoformat(),
            }
        
        return {"error": f"Metric {metric} not supported"}

    async def get_earnings_calendar_analysis(
        self, 
        start_date: date, 
        end_date: date
    ) -> Dict[str, Any]:
        """Get detailed earnings calendar with predictions and analysis"""
        
        earnings = await self.db.query(EarningsEvent).filter(
            and_(
                EarningsEvent.earnings_date >= start_date,
                EarningsEvent.earnings_date <= end_date,
            )
        ).order_by(EarningsEvent.earnings_date).all()
        
        # Get predictions for these earnings
        predictions = await self.db.query(Prediction).filter(
            and_(
                Prediction.target_date >= start_date,
                Prediction.target_date <= end_date,
            )
        ).all()
        
        # Create lookup for predictions
        prediction_lookup = {
            f"{p.company_symbol}_{p.target_date}": p for p in predictions
        }
        
        calendar_items = []
        for earning in earnings:
            prediction_key = f"{earning.company_symbol}_{earning.earnings_date.date() + timedelta(days=1)}"
            prediction = prediction_lookup.get(prediction_key)
            
            calendar_items.append({
                "company_symbol": earning.company_symbol,
                "earnings_date": earning.earnings_date.isoformat(),
                "quarter": earning.quarter,
                "year": earning.year,
                "expected_eps": earning.expected_eps,
                "has_prediction": prediction is not None,
                "prediction_confidence": prediction.confidence_score if prediction else None,
                "predicted_direction": prediction.direction if prediction else None,
                "predicted_return": prediction.predicted_return if prediction else None,
            })
        
        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_earnings": len(calendar_items),
            "with_predictions": sum(1 for item in calendar_items if item["has_prediction"]),
            "calendar": calendar_items,
        }

    async def get_company_profile(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive company analytics profile"""
        
        # Get company info
        company = await self.db.query(Company).filter(
            Company.symbol == symbol
        ).first()
        
        if not company:
            return {"error": f"Company {symbol} not found"}
        
        # Get recent earnings
        recent_earnings = await self.db.query(EarningsEvent).filter(
            EarningsEvent.company_symbol == symbol
        ).order_by(desc(EarningsEvent.earnings_date)).limit(8).all()
        
        # Get recent analyst ratings
        recent_ratings = await self.db.query(AnalystRating).filter(
            AnalystRating.company_symbol == symbol
        ).order_by(desc(AnalystRating.rating_date)).limit(10).all()
        
        # Get recent predictions
        recent_predictions = await self.db.query(Prediction).filter(
            Prediction.company_symbol == symbol
        ).order_by(desc(Prediction.prediction_date)).limit(5).all()
        
        # Calculate performance metrics
        earnings_stats = self._calculate_earnings_stats(recent_earnings)
        analyst_stats = self._calculate_analyst_stats(recent_ratings)
        prediction_stats = self._calculate_prediction_stats(recent_predictions)
        
        return {
            "company": {
                "symbol": company.symbol,
                "name": company.name,
                "sector": company.sector,
                "industry": company.industry,
                "market_cap": company.market_cap,
                "pe_ratio": company.pe_ratio,
                "eps": company.eps,
            },
            "earnings_performance": earnings_stats,
            "analyst_coverage": analyst_stats,
            "prediction_history": prediction_stats,
            "recent_earnings": [
                {
                    "date": e.earnings_date.isoformat() if e.earnings_date else None,
                    "quarter": e.quarter,
                    "year": e.year,
                    "surprise_percentage": e.surprise_percentage,
                    "return_1d": e.return_1d,
                }
                for e in recent_earnings[:4]
            ],
            "timestamp": datetime.now().isoformat(),
        }

    async def get_insider_trading_analysis(
        self, 
        symbol: Optional[str] = None, 
        days_back: int = 90,
        transaction_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get insider trading analysis"""
        
        start_date = date.today() - timedelta(days=days_back)
        
        query = self.db.query(InsiderTrading).filter(
            InsiderTrading.transaction_date >= start_date
        )
        
        if symbol:
            query = query.filter(InsiderTrading.company_symbol == symbol)
        
        if transaction_type:
            query = query.filter(InsiderTrading.transaction_type == transaction_type)
        
        transactions = await query.order_by(desc(InsiderTrading.transaction_date)).all()
        
        if not transactions:
            return {
                "total_transactions": 0,
                "analysis": "No insider trading data found for the specified criteria",
            }
        
        # Analyze transactions
        buy_transactions = [t for t in transactions if t.transaction_type == "BUY"]
        sell_transactions = [t for t in transactions if t.transaction_type == "SELL"]
        
        total_buy_value = sum(t.total_value for t in buy_transactions)
        total_sell_value = sum(t.total_value for t in sell_transactions)
        
        return {
            "period_days": days_back,
            "symbol": symbol,
            "total_transactions": len(transactions),
            "buy_transactions": len(buy_transactions),
            "sell_transactions": len(sell_transactions),
            "total_buy_value": total_buy_value,
            "total_sell_value": total_sell_value,
            "net_insider_sentiment": "BULLISH" if total_buy_value > total_sell_value else "BEARISH",
            "recent_transactions": [
                {
                    "company_symbol": t.company_symbol,
                    "insider_name": t.insider_name,
                    "transaction_type": t.transaction_type,
                    "shares": t.shares,
                    "total_value": t.total_value,
                    "transaction_date": t.transaction_date.isoformat(),
                }
                for t in transactions[:10]
            ],
        }

    def _calculate_earnings_stats(self, earnings: List[EarningsEvent]) -> Dict[str, Any]:
        """Calculate earnings performance statistics"""
        
        if not earnings:
            return {"total_events": 0}
        
        surprises = [e.surprise_percentage for e in earnings if e.surprise_percentage is not None]
        returns = [e.return_1d for e in earnings if e.return_1d is not None]
        
        beats = sum(1 for s in surprises if s > 0)
        misses = sum(1 for s in surprises if s < 0)
        
        return {
            "total_events": len(earnings),
            "beat_count": beats,
            "miss_count": misses,
            "beat_rate": beats / len(surprises) if surprises else 0,
            "avg_surprise": np.mean(surprises) if surprises else 0,
            "avg_return_1d": np.mean(returns) if returns else 0,
            "return_volatility": np.std(returns) if len(returns) > 1 else 0,
        }

    def _calculate_analyst_stats(self, ratings: List[AnalystRating]) -> Dict[str, Any]:
        """Calculate analyst coverage statistics"""
        
        if not ratings:
            return {"total_ratings": 0}
        
        buy_ratings = sum(1 for r in ratings if r.rating.upper() in ['BUY', 'STRONG BUY'])
        hold_ratings = sum(1 for r in ratings if r.rating.upper() == 'HOLD')
        sell_ratings = sum(1 for r in ratings if r.rating.upper() in ['SELL', 'STRONG SELL'])
        
        target_prices = [r.target_price for r in ratings if r.target_price]
        
        return {
            "total_ratings": len(ratings),
            "buy_ratings": buy_ratings,
            "hold_ratings": hold_ratings,
            "sell_ratings": sell_ratings,
            "consensus": "BUY" if buy_ratings > hold_ratings and buy_ratings > sell_ratings else 
                        "SELL" if sell_ratings > hold_ratings and sell_ratings > buy_ratings else "HOLD",
            "avg_target_price": np.mean(target_prices) if target_prices else None,
            "target_price_range": {
                "min": min(target_prices) if target_prices else None,
                "max": max(target_prices) if target_prices else None,
            },
        }

    def _calculate_prediction_stats(self, predictions: List[Prediction]) -> Dict[str, Any]:
        """Calculate prediction performance statistics"""
        
        if not predictions:
            return {"total_predictions": 0}
        
        completed_predictions = [p for p in predictions if p.actual_return is not None]
        
        if not completed_predictions:
            return {
                "total_predictions": len(predictions),
                "completed_predictions": 0,
            }
        
        # Calculate accuracy metrics
        direction_correct = sum(
            1 for p in completed_predictions
            if (p.predicted_return > 0 and p.actual_return > 0) or
               (p.predicted_return < 0 and p.actual_return < 0)
        )
        
        accuracies = [p.prediction_accuracy for p in completed_predictions if p.prediction_accuracy]
        
        return {
            "total_predictions": len(predictions),
            "completed_predictions": len(completed_predictions),
            "direction_accuracy": direction_correct / len(completed_predictions),
            "avg_accuracy": np.mean(accuracies) if accuracies else 0,
            "avg_confidence": np.mean([p.confidence_score for p in predictions]),
        }