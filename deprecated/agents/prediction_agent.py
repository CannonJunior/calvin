from typing import Dict, List, Any, Optional
import json
from datetime import datetime, timedelta

from agents.base_agent import BaseAgent


class PredictionAgent(BaseAgent):
    def __init__(self):
        super().__init__(model_name="llama3.1:8b", max_tokens=1500, temperature=0.2)
        
    def get_system_prompt(self) -> str:
        return """You are an expert quantitative analyst specializing in stock price prediction for S&P 500 companies. Your role is to:

1. Generate detailed explanations for stock price predictions
2. Analyze prediction confidence and uncertainty
3. Identify key factors driving predictions
4. Assess prediction risks and limitations
5. Provide probabilistic forecasts with confidence intervals

Guidelines:
- Be precise about prediction methodology and assumptions
- Clearly explain uncertainty and risk factors
- Quantify confidence levels with specific reasoning
- Highlight both supporting and contradicting evidence
- Reference historical precedents and patterns
- Use statistical and financial terminology accurately
- Provide actionable insights for decision-making
- Always include appropriate disclaimers about prediction limitations"""

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process prediction-related requests"""
        
        request_type = input_data.get("request_type", "explain_prediction")
        
        if request_type == "explain_prediction":
            return await self._explain_prediction(input_data)
        elif request_type == "generate_prediction":
            return await self._generate_prediction(input_data)
        elif request_type == "assess_confidence":
            return await self._assess_confidence(input_data)
        elif request_type == "risk_analysis":
            return await self._analyze_risks(input_data)
        else:
            return await self._general_prediction_analysis(input_data)
    
    async def _explain_prediction(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Explain a specific prediction in detail"""
        
        prediction_data = input_data.get("prediction_data", {})
        symbol = prediction_data.get("company_symbol", "")
        predicted_return = prediction_data.get("predicted_return", 0)
        confidence = prediction_data.get("confidence_score", 0)
        features = prediction_data.get("features_used", {})
        model_version = prediction_data.get("model_version", "")
        
        if not prediction_data:
            return {
                "explanation": "No prediction data provided",
                "confidence": 0.0,
                "key_factors": [],
                "risks": []
            }
        
        prompt = f"""Explain this stock prediction for {symbol} in detail:

Prediction Details:
- Symbol: {symbol}
- Predicted Return: {predicted_return:.2%}
- Model Confidence: {confidence:.1%}
- Model Version: {model_version}

Key Features Used in Prediction:
"""
        
        for feature, value in features.items():
            prompt += f"- {feature}: {value}\n"
        
        prompt += f"""

Provide a comprehensive explanation including:
1. Why the model predicts a {predicted_return:.2%} return
2. Which factors are most influential in this prediction
3. How the confidence level of {confidence:.1%} was determined
4. Historical precedents supporting this prediction
5. Key assumptions and their validity
6. Potential scenarios that could invalidate the prediction
7. Risk factors and uncertainty sources
8. Recommended monitoring points
9. Comparison to typical prediction accuracy for similar scenarios
10. Investment implications and suggested actions

Be specific about the quantitative reasoning and provide context for the prediction."""

        try:
            result = await self._call_ollama(prompt, self.get_system_prompt())
            explanation_text = result.get("response", "")
            
            # Extract structured insights
            key_factors = self._extract_key_factors(explanation_text, features)
            risks = self._extract_risks(explanation_text)
            monitoring_points = self._extract_monitoring_points(explanation_text)
            
            return {
                "explanation": explanation_text,
                "confidence": confidence,
                "key_factors": key_factors,
                "risks": risks,
                "monitoring_points": monitoring_points,
                "prediction_summary": {
                    "symbol": symbol,
                    "return": predicted_return,
                    "direction": "UP" if predicted_return > 0 else "DOWN" if predicted_return < 0 else "NEUTRAL",
                    "magnitude": abs(predicted_return),
                    "confidence_level": self._categorize_confidence(confidence),
                },
                "timestamp": datetime.now().isoformat(),
                "processing_time": result.get("total_duration", 0) / 1000000,
            }
            
        except Exception as e:
            return {
                "explanation": f"Error explaining prediction: {str(e)}",
                "confidence": 0.0,
                "key_factors": [],
                "risks": ["Error in analysis"],
                "error": str(e)
            }
    
    async def _generate_prediction(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a new prediction with reasoning"""
        
        symbol = input_data.get("symbol", "")
        market_data = input_data.get("market_data", {})
        earnings_data = input_data.get("earnings_data", [])
        analyst_data = input_data.get("analyst_data", [])
        
        prompt = f"""Generate a stock price prediction for {symbol} based on the following data:

Company: {symbol}

Market Data:
- Sector: {market_data.get('sector', 'N/A')}
- Market Cap: ${market_data.get('market_cap', 0):,.0f}M
- P/E Ratio: {market_data.get('pe_ratio', 'N/A')}
- Current EPS: ${market_data.get('eps', 'N/A')}

Recent Earnings Performance:
"""
        
        for i, earning in enumerate(earnings_data[:4]):
            prompt += f"""
Quarter {i+1}:
- Surprise: {earning.get('surprise_percentage', 'N/A')}%
- 1-Day Return: {earning.get('return_1d', 'N/A')}%
- Relative Return: {earning.get('relative_return_1d', 'N/A')}%
"""

        prompt += f"""
Analyst Ratings (Recent):
"""
        for rating in analyst_data[:3]:
            prompt += f"- {rating.get('analyst_firm', 'Unknown')}: {rating.get('rating', 'N/A')} (Target: ${rating.get('target_price', 'N/A')})\n"

        prompt += """
Based on this information, provide:
1. A specific return prediction for the next earnings announcement (+1 day)
2. Confidence level (0-100%)
3. Key factors supporting your prediction
4. Risk factors that could invalidate the prediction
5. Comparable historical scenarios
6. Uncertainty analysis and potential range of outcomes
7. Market conditions assumptions
8. Timeline considerations

Format your response with clear reasoning and quantitative justification."""

        try:
            result = await self._call_ollama(prompt, self.get_system_prompt())
            prediction_text = result.get("response", "")
            
            # Extract prediction details
            predicted_return = self._extract_return_prediction(prediction_text)
            confidence = self._extract_confidence_score(prediction_text)
            key_factors = self._extract_supporting_factors(prediction_text)
            risks = self._extract_risks(prediction_text)
            
            return {
                "prediction": prediction_text,
                "predicted_return": predicted_return,
                "confidence_score": confidence,
                "direction": "UP" if predicted_return > 0 else "DOWN" if predicted_return < 0 else "NEUTRAL",
                "key_factors": key_factors,
                "risk_factors": risks,
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
                "processing_time": result.get("total_duration", 0) / 1000000,
            }
            
        except Exception as e:
            return {
                "prediction": f"Error generating prediction: {str(e)}",
                "predicted_return": 0.0,
                "confidence_score": 0.0,
                "direction": "NEUTRAL",
                "error": str(e)
            }
    
    async def _assess_confidence(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess confidence in a prediction"""
        
        prediction_data = input_data.get("prediction_data", {})
        historical_accuracy = input_data.get("historical_accuracy", {})
        
        prompt = f"""Assess the confidence level for this prediction:

Prediction: {prediction_data.get('predicted_return', 0):.2%} return
Current Confidence: {prediction_data.get('confidence_score', 0):.1%}

Historical Model Performance:
- Overall Accuracy: {historical_accuracy.get('overall_accuracy', 'N/A')}
- Similar Scenarios Accuracy: {historical_accuracy.get('similar_scenarios_accuracy', 'N/A')}
- Recent Performance: {historical_accuracy.get('recent_performance', 'N/A')}

Evaluate:
1. Is the current confidence level appropriate?
2. What factors increase/decrease confidence?
3. How does this compare to typical prediction confidence?
4. What additional data would improve confidence?
5. Confidence interval estimation
6. Recommended confidence adjustments

Provide specific reasoning for confidence assessment."""

        try:
            result = await self._call_ollama(prompt, self.get_system_prompt())
            
            return {
                "confidence_assessment": result.get("response", ""),
                "recommended_confidence": self._extract_recommended_confidence(result.get("response", "")),
                "confidence_factors": self._extract_confidence_factors(result.get("response", "")),
                "timestamp": datetime.now().isoformat(),
            }
            
        except Exception as e:
            return {
                "confidence_assessment": f"Error assessing confidence: {str(e)}",
                "error": str(e)
            }
    
    def _extract_key_factors(self, text: str, features: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract key factors from explanation text"""
        factors = []
        
        # Look for feature mentions in text
        for feature, value in features.items():
            if feature.lower().replace("_", " ") in text.lower():
                factors.append({
                    "factor": feature.replace("_", " ").title(),
                    "value": value,
                    "importance": "high" if "important" in text.lower() or "key" in text.lower() else "medium"
                })
        
        # Add some common factors based on keywords
        factor_keywords = {
            "earnings surprise": "Earnings surprise percentage",
            "beat rate": "Historical beat rate",
            "analyst sentiment": "Analyst sentiment",
            "volatility": "Stock volatility",
            "market conditions": "Market conditions",
        }
        
        text_lower = text.lower()
        for keyword, factor_name in factor_keywords.items():
            if keyword in text_lower and not any(f["factor"] == factor_name for f in factors):
                factors.append({
                    "factor": factor_name,
                    "value": "See analysis",
                    "importance": "medium"
                })
        
        return factors[:7]  # Limit to top 7 factors
    
    def _extract_risks(self, text: str) -> List[str]:
        """Extract risk factors from text"""
        risks = []
        
        risk_keywords = [
            "market volatility", "economic uncertainty", "sector rotation",
            "analyst downgrades", "guidance miss", "competitive pressure",
            "regulatory risk", "macroeconomic factors", "earnings miss",
            "technical breakdown", "momentum reversal"
        ]
        
        text_lower = text.lower()
        for risk in risk_keywords:
            if risk in text_lower:
                risks.append(risk.title())
        
        return risks[:5]  # Limit to 5 risks
    
    def _extract_monitoring_points(self, text: str) -> List[str]:
        """Extract monitoring points from text"""
        monitoring = []
        
        monitoring_keywords = [
            "earnings guidance", "analyst revisions", "sector performance",
            "market sentiment", "volume patterns", "technical levels",
            "insider trading", "institutional flow"
        ]
        
        text_lower = text.lower()
        for point in monitoring_keywords:
            if point in text_lower:
                monitoring.append(point.title())
        
        return monitoring[:6]  # Limit to 6 monitoring points
    
    def _categorize_confidence(self, confidence: float) -> str:
        """Categorize confidence level"""
        if confidence >= 0.8:
            return "High"
        elif confidence >= 0.6:
            return "Medium"
        elif confidence >= 0.4:
            return "Low"
        else:
            return "Very Low"
    
    def _extract_return_prediction(self, text: str) -> float:
        """Extract return prediction from text"""
        import re
        
        # Look for percentage patterns
        patterns = [
            r'predict[^.]*?([+-]?\d+\.?\d*)%',
            r'return[^.]*?([+-]?\d+\.?\d*)%',
            r'expect[^.]*?([+-]?\d+\.?\d*)%'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return float(match.group(1)) / 100
        
        return 0.0  # Default if no prediction found
    
    def _extract_confidence_score(self, text: str) -> float:
        """Extract confidence score from text"""
        import re
        
        confidence_pattern = r'confidence[^.]*?(\d+\.?\d*)%'
        match = re.search(confidence_pattern, text.lower())
        
        if match:
            return float(match.group(1)) / 100
        
        return 0.6  # Default confidence
    
    async def _general_prediction_analysis(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """General prediction analysis"""
        return await self._explain_prediction(input_data)