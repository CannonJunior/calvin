from typing import Dict, List, Any, Optional
import json
from datetime import datetime, timedelta

from agents.base_agent import BaseAgent


class AnalysisAgent(BaseAgent):
    def __init__(self):
        super().__init__(model_name="llama3.1:8b", max_tokens=1500, temperature=0.3)
        
    def get_system_prompt(self) -> str:
        return """You are an expert financial analyst specializing in earnings pattern analysis for S&P 500 companies. Your role is to:

1. Analyze historical earnings data and identify patterns
2. Extract meaningful insights from financial metrics
3. Identify correlations between earnings performance and stock price movements
4. Provide evidence-based analysis with specific data points
5. Focus on quantitative analysis while explaining the underlying factors

Guidelines:
- Be precise and data-driven in your analysis
- Highlight statistical significance of patterns
- Explain both positive and negative indicators
- Reference specific historical events when relevant
- Provide actionable insights for prediction models
- Use financial terminology accurately
- Keep responses concise but comprehensive"""

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze earnings patterns for a company"""
        
        symbol = input_data.get("symbol")
        analysis_type = input_data.get("analysis_type", "earnings_pattern")
        earnings_data = input_data.get("earnings_data", [])
        market_data = input_data.get("market_data", {})
        
        if analysis_type == "earnings_pattern":
            return await self._analyze_earnings_patterns(symbol, earnings_data, market_data)
        elif analysis_type == "surprise_correlation":
            return await self._analyze_surprise_correlation(symbol, earnings_data)
        elif analysis_type == "seasonal_trends":
            return await self._analyze_seasonal_trends(symbol, earnings_data)
        elif analysis_type == "volatility_analysis":
            return await self._analyze_volatility_patterns(symbol, earnings_data, market_data)
        else:
            return await self._general_analysis(symbol, earnings_data, market_data)
    
    async def _analyze_earnings_patterns(
        self, 
        symbol: str, 
        earnings_data: List[Dict], 
        market_data: Dict
    ) -> Dict[str, Any]:
        """Analyze earnings patterns and stock performance correlation"""
        
        # Prepare data summary for analysis
        if not earnings_data:
            return {
                "analysis": f"No earnings data available for {symbol}",
                "confidence": 0.0,
                "key_insights": [],
                "patterns": {}
            }
        
        # Calculate key metrics
        total_earnings = len(earnings_data)
        beats = sum(1 for e in earnings_data if e.get("surprise_percentage", 0) > 0)
        beat_rate = beats / total_earnings if total_earnings > 0 else 0
        
        avg_surprise = sum(e.get("surprise_percentage", 0) for e in earnings_data) / total_earnings if total_earnings > 0 else 0
        
        returns_1d = [e.get("return_1d") for e in earnings_data if e.get("return_1d") is not None]
        avg_return_1d = sum(returns_1d) / len(returns_1d) if returns_1d else 0
        
        # Create analysis prompt
        prompt = f"""Analyze the earnings patterns for {symbol} based on the following data:

Company: {symbol}
Total Earnings Events: {total_earnings}
Beat Rate: {beat_rate:.1%}
Average Earnings Surprise: {avg_surprise:.1f}%
Average 1-Day Return After Earnings: {avg_return_1d:.2%}

Historical Earnings Data (most recent first):
"""
        
        for i, earning in enumerate(earnings_data[:8]):  # Limit to most recent 8 earnings
            prompt += f"""
Event {i+1}:
- Date: {earning.get('earnings_date', 'N/A')}
- Quarter: {earning.get('quarter', 'N/A')} {earning.get('year', 'N/A')}
- Actual EPS: ${earning.get('actual_eps', 'N/A')}
- Expected EPS: ${earning.get('expected_eps', 'N/A')}
- Surprise: {earning.get('surprise_percentage', 'N/A')}%
- Stock Return (1D): {earning.get('return_1d', 'N/A')}%
- Relative to Market: {earning.get('relative_return_1d', 'N/A')}%
"""

        prompt += f"""

Provide a comprehensive analysis focusing on:
1. Key patterns in earnings surprises and stock reactions
2. Correlation between surprise magnitude and stock performance
3. Consistency of market reactions (positive surprises = positive returns?)
4. Seasonal or quarterly trends
5. Volatility patterns around earnings
6. Relative performance vs market/sector
7. Predictive indicators for future earnings reactions

Format your response as structured analysis with specific insights and recommendations."""

        try:
            result = await self._call_ollama(prompt, self.get_system_prompt())
            
            analysis_text = result.get("response", "")
            
            # Extract key metrics for structured response
            patterns = {
                "beat_rate": beat_rate,
                "avg_surprise": avg_surprise,
                "avg_return_1d": avg_return_1d,
                "total_events": total_earnings,
                "volatility": self._calculate_volatility(returns_1d),
                "consistency_score": self._calculate_consistency_score(earnings_data),
            }
            
            # Extract key insights (simple keyword-based extraction)
            insights = self._extract_insights(analysis_text)
            
            return {
                "analysis": analysis_text,
                "confidence": self._calculate_confidence(earnings_data),
                "key_insights": insights,
                "patterns": patterns,
                "processing_time": result.get("total_duration", 0) / 1000000,  # Convert to seconds
                "timestamp": datetime.now().isoformat(),
            }
            
        except Exception as e:
            return {
                "analysis": f"Error analyzing earnings patterns: {str(e)}",
                "confidence": 0.0,
                "key_insights": [],
                "patterns": {},
                "error": str(e)
            }
    
    async def _analyze_surprise_correlation(
        self, 
        symbol: str, 
        earnings_data: List[Dict]
    ) -> Dict[str, Any]:
        """Analyze correlation between earnings surprises and stock returns"""
        
        surprise_return_pairs = [
            (e.get("surprise_percentage", 0), e.get("return_1d", 0))
            for e in earnings_data
            if e.get("surprise_percentage") is not None and e.get("return_1d") is not None
        ]
        
        if len(surprise_return_pairs) < 3:
            return {
                "analysis": "Insufficient data for surprise correlation analysis",
                "confidence": 0.0,
                "correlation": None
            }
        
        # Calculate correlation coefficient
        correlation = self._calculate_correlation(surprise_return_pairs)
        
        prompt = f"""Analyze the correlation between earnings surprises and stock returns for {symbol}:

Data Points: {len(surprise_return_pairs)}
Calculated Correlation: {correlation:.3f}

Surprise-Return Pairs:
"""
        for surprise, return_val in surprise_return_pairs:
            prompt += f"Surprise: {surprise:.1f}%, Return: {return_val:.2f}%\n"
        
        prompt += """
Provide analysis on:
1. Strength and significance of the correlation
2. Outliers or unusual patterns
3. Market efficiency implications
4. Predictive value for future earnings
5. Comparison to typical market behavior
"""

        try:
            result = await self._call_ollama(prompt, self.get_system_prompt())
            
            return {
                "analysis": result.get("response", ""),
                "confidence": min(1.0, len(surprise_return_pairs) / 10),
                "correlation": correlation,
                "data_points": len(surprise_return_pairs),
                "timestamp": datetime.now().isoformat(),
            }
            
        except Exception as e:
            return {
                "analysis": f"Error in surprise correlation analysis: {str(e)}",
                "confidence": 0.0,
                "correlation": None,
                "error": str(e)
            }
    
    def _calculate_volatility(self, returns: List[float]) -> float:
        """Calculate volatility of returns"""
        if len(returns) < 2:
            return 0.0
        
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / (len(returns) - 1)
        return variance ** 0.5
    
    def _calculate_consistency_score(self, earnings_data: List[Dict]) -> float:
        """Calculate consistency score based on earnings performance"""
        if not earnings_data:
            return 0.0
        
        # Score based on beat rate and return consistency
        surprises = [e.get("surprise_percentage", 0) for e in earnings_data]
        returns = [e.get("return_1d", 0) for e in earnings_data if e.get("return_1d") is not None]
        
        if not returns:
            return 0.0
        
        # Consistency is inverse of volatility, normalized
        volatility = self._calculate_volatility(returns)
        consistency = max(0, 1 - (volatility / 10))  # Normalize assuming 10% is high volatility
        
        return consistency
    
    def _calculate_correlation(self, pairs: List[tuple]) -> float:
        """Calculate Pearson correlation coefficient"""
        if len(pairs) < 2:
            return 0.0
        
        x_values = [pair[0] for pair in pairs]
        y_values = [pair[1] for pair in pairs]
        
        n = len(pairs)
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in pairs)
        sum_x2 = sum(x * x for x in x_values)
        sum_y2 = sum(y * y for y in y_values)
        
        numerator = n * sum_xy - sum_x * sum_y
        denominator = ((n * sum_x2 - sum_x ** 2) * (n * sum_y2 - sum_y ** 2)) ** 0.5
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    def _calculate_confidence(self, earnings_data: List[Dict]) -> float:
        """Calculate confidence score based on data quality and quantity"""
        if not earnings_data:
            return 0.0
        
        # Base confidence on data quantity and completeness
        data_points = len(earnings_data)
        complete_records = sum(
            1 for e in earnings_data
            if e.get("surprise_percentage") is not None and e.get("return_1d") is not None
        )
        
        completeness = complete_records / data_points if data_points > 0 else 0
        quantity_score = min(1.0, data_points / 8)  # 8 quarters = 2 years
        
        return (completeness + quantity_score) / 2
    
    def _extract_insights(self, analysis_text: str) -> List[str]:
        """Extract key insights from analysis text"""
        insights = []
        
        # Simple keyword-based extraction (in production, use more sophisticated NLP)
        keywords = {
            "strong correlation": "Strong correlation between surprises and returns",
            "weak correlation": "Weak correlation between surprises and returns",
            "consistent": "Consistent earnings performance pattern",
            "volatile": "High volatility in post-earnings returns",
            "beats expectations": "Company frequently beats expectations",
            "misses expectations": "Company frequently misses expectations",
            "seasonal": "Seasonal trends in earnings performance",
            "outperforms": "Stock outperforms market after earnings",
            "underperforms": "Stock underperforms market after earnings",
        }
        
        analysis_lower = analysis_text.lower()
        for keyword, insight in keywords.items():
            if keyword in analysis_lower:
                insights.append(insight)
        
        return insights[:5]  # Limit to top 5 insights
    
    async def _general_analysis(
        self, 
        symbol: str, 
        earnings_data: List[Dict], 
        market_data: Dict
    ) -> Dict[str, Any]:
        """Perform general earnings analysis"""
        return await self._analyze_earnings_patterns(symbol, earnings_data, market_data)