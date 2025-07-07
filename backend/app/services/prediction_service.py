from typing import Dict, List, Optional, Any
from datetime import datetime, date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, desc
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import joblib
import json

from app.models.company import Company, EarningsEvent, Prediction, AnalystRating
from app.services.agent_orchestrator import AgentOrchestrator


class PredictionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.model_version = "v1.0.0"
        self.scaler = StandardScaler()
        self.agent_orchestrator = AgentOrchestrator(db)

    async def generate_prediction(
        self,
        symbol: str,
        target_date: date,
    ) -> Prediction:
        """Generate a new prediction for a symbol"""
        
        # Get company data
        company = await self.db.query(Company).filter(
            Company.symbol == symbol
        ).first()
        
        if not company:
            raise ValueError(f"Company {symbol} not found")
        
        # Extract features
        features = await self._extract_features(symbol, target_date)
        
        # Generate prediction using ML model
        predicted_return, confidence = await self._predict_return(features)
        
        # Determine direction
        direction = self._get_direction(predicted_return)
        
        # Get AI-generated reasoning
        reasoning = await self._generate_reasoning(symbol, features, predicted_return)
        
        # Find similar scenarios using RAG
        similar_scenarios = await self._find_similar_scenarios(symbol, features)
        
        # Create prediction record
        prediction = Prediction(
            company_symbol=symbol,
            prediction_date=datetime.now(),
            target_date=target_date,
            predicted_return=predicted_return,
            confidence_score=confidence,
            direction=direction,
            model_version=self.model_version,
            features_used=features,
            reasoning=reasoning,
            similar_scenarios=similar_scenarios,
        )
        
        self.db.add(prediction)
        await self.db.commit()
        await self.db.refresh(prediction)
        
        return prediction

    async def _extract_features(self, symbol: str, target_date: date) -> Dict[str, Any]:
        """Extract features for prediction model"""
        features = {}
        
        # Get recent earnings events
        recent_earnings = await self.db.query(EarningsEvent).filter(
            and_(
                EarningsEvent.company_symbol == symbol,
                EarningsEvent.earnings_date <= target_date,
            )
        ).order_by(desc(EarningsEvent.earnings_date)).limit(8).all()
        
        if recent_earnings:
            # Calculate historical performance metrics
            surprises = [e.surprise_percentage for e in recent_earnings if e.surprise_percentage]
            returns_1d = [e.return_1d for e in recent_earnings if e.return_1d]
            
            features.update({
                "avg_surprise_percentage": np.mean(surprises) if surprises else 0,
                "surprise_std": np.std(surprises) if len(surprises) > 1 else 0,
                "avg_return_1d": np.mean(returns_1d) if returns_1d else 0,
                "return_volatility": np.std(returns_1d) if len(returns_1d) > 1 else 0,
                "beat_rate": sum(1 for s in surprises if s > 0) / len(surprises) if surprises else 0,
                "earnings_count": len(recent_earnings),
            })
            
            # Latest earnings metrics
            latest = recent_earnings[0]
            features.update({
                "last_surprise_percentage": latest.surprise_percentage or 0,
                "last_return_1d": latest.return_1d or 0,
                "days_since_last_earnings": (target_date - latest.earnings_date.date()).days,
            })
        
        # Get analyst ratings
        analyst_ratings = await self.db.query(AnalystRating).filter(
            and_(
                AnalystRating.company_symbol == symbol,
                AnalystRating.rating_date >= target_date - timedelta(days=30),
            )
        ).all()
        
        if analyst_ratings:
            # Calculate analyst sentiment
            buy_ratings = sum(1 for r in analyst_ratings if r.rating.upper() in ['BUY', 'STRONG BUY'])
            hold_ratings = sum(1 for r in analyst_ratings if r.rating.upper() == 'HOLD')
            sell_ratings = sum(1 for r in analyst_ratings if r.rating.upper() in ['SELL', 'STRONG SELL'])
            
            total_ratings = len(analyst_ratings)
            features.update({
                "analyst_buy_ratio": buy_ratings / total_ratings,
                "analyst_hold_ratio": hold_ratings / total_ratings,
                "analyst_sell_ratio": sell_ratings / total_ratings,
                "analyst_rating_count": total_ratings,
            })
            
            # Target price analysis
            targets = [r.target_price for r in analyst_ratings if r.target_price and r.current_price]
            if targets:
                avg_upside = np.mean([(t - r.current_price) / r.current_price for r, t in 
                                     zip(analyst_ratings, targets) if r.current_price])
                features["avg_analyst_upside"] = avg_upside
        
        # Add market context features
        # Note: In a real implementation, you'd fetch market data here
        features.update({
            "is_earnings_season": self._is_earnings_season(target_date),
            "quarter": (target_date.month - 1) // 3 + 1,
            "month": target_date.month,
            "day_of_week": target_date.weekday(),
        })
        
        return features

    async def _predict_return(self, features: Dict[str, Any]) -> tuple[float, float]:
        """Predict stock return using ML model"""
        # Convert features to numpy array
        feature_names = [
            "avg_surprise_percentage", "surprise_std", "avg_return_1d", "return_volatility",
            "beat_rate", "earnings_count", "last_surprise_percentage", "last_return_1d",
            "days_since_last_earnings", "analyst_buy_ratio", "analyst_hold_ratio",
            "analyst_sell_ratio", "analyst_rating_count", "avg_analyst_upside",
            "is_earnings_season", "quarter", "month", "day_of_week"
        ]
        
        # Fill missing features with defaults
        feature_vector = []
        for name in feature_names:
            feature_vector.append(features.get(name, 0))
        
        # For now, use a simple model (in production, load pre-trained model)
        # This is a placeholder - you'd load your trained model here
        try:
            # model = joblib.load('path/to/trained_model.pkl')
            # predicted_return = model.predict([feature_vector])[0]
            
            # Simplified prediction logic for demo
            surprise_weight = features.get("avg_surprise_percentage", 0) * 0.002
            analyst_weight = features.get("analyst_buy_ratio", 0.5) * 0.01
            historical_weight = features.get("avg_return_1d", 0) * 0.5
            
            predicted_return = surprise_weight + analyst_weight + historical_weight
            
            # Add some randomness to simulate model uncertainty
            confidence = min(0.95, max(0.1, 0.7 + abs(predicted_return) * 10))
            
        except Exception:
            # Fallback prediction
            predicted_return = 0.001  # Small positive bias
            confidence = 0.5
        
        return predicted_return, confidence

    async def _generate_reasoning(
        self,
        symbol: str,
        features: Dict[str, Any],
        predicted_return: float,
    ) -> str:
        """Generate AI explanation for the prediction"""
        try:
            reasoning_prompt = f"""
            Explain why the model predicts a {predicted_return:.2%} return for {symbol}.
            
            Key factors:
            - Average earnings surprise: {features.get('avg_surprise_percentage', 0):.1f}%
            - Historical beat rate: {features.get('beat_rate', 0):.1%}
            - Average 1-day return after earnings: {features.get('avg_return_1d', 0):.2%}
            - Analyst buy ratio: {features.get('analyst_buy_ratio', 0):.1%}
            - Days since last earnings: {features.get('days_since_last_earnings', 0)}
            
            Provide a concise explanation focusing on the most important factors.
            """
            
            response = await self.agent_orchestrator.process_query(
                query=reasoning_prompt,
                agent_type="prediction",
                context={"symbol": symbol, "features": features},
            )
            
            return response.response if response else "Prediction based on historical patterns and analyst sentiment."
            
        except Exception as e:
            return f"Prediction based on quantitative analysis. Model confidence: {features.get('confidence', 0.5):.1%}"

    async def _find_similar_scenarios(
        self,
        symbol: str,
        features: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Find similar historical scenarios using RAG"""
        try:
            similar = await self.agent_orchestrator.find_similar_scenarios(
                symbol=symbol,
                scenario_type="earnings",
                limit=3,
            )
            return similar if similar else []
        except Exception:
            return []

    def _get_direction(self, predicted_return: float) -> str:
        """Determine prediction direction"""
        if predicted_return > 0.005:  # > 0.5%
            return "UP"
        elif predicted_return < -0.005:  # < -0.5%
            return "DOWN"
        else:
            return "NEUTRAL"

    def _is_earnings_season(self, target_date: date) -> bool:
        """Check if target date is during earnings season"""
        # Earnings seasons: Jan-Feb, Apr-May, Jul-Aug, Oct-Nov
        month = target_date.month
        return month in [1, 2, 4, 5, 7, 8, 10, 11]

    async def update_prediction_accuracy(self, prediction_id: str, actual_return: float):
        """Update prediction with actual results"""
        prediction = await self.db.query(Prediction).filter(
            Prediction.id == prediction_id
        ).first()
        
        if not prediction:
            raise ValueError("Prediction not found")
        
        prediction.actual_return = actual_return
        
        # Calculate accuracy (inverse of percentage error)
        error = abs(prediction.predicted_return - actual_return)
        max_error = max(abs(prediction.predicted_return), abs(actual_return), 0.01)
        accuracy = max(0, 1 - (error / max_error))
        
        prediction.prediction_accuracy = accuracy
        
        await self.db.commit()
        await self.db.refresh(prediction)
        
        return prediction