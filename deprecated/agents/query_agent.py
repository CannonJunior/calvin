from typing import Dict, List, Any, Optional
import json
from datetime import datetime, timedelta

from agents.base_agent import BaseAgent


class QueryAgent(BaseAgent):
    def __init__(self):
        super().__init__(model_name="qwen2.5:7b", max_tokens=2000, temperature=0.5)
        
    def get_system_prompt(self) -> str:
        return """You are an expert financial data analyst and query assistant specializing in S&P 500 companies and stock market analysis. Your role is to:

1. Answer questions about company financial data and performance
2. Provide insights on market trends and patterns
3. Find and explain historical scenarios and precedents
4. Help users explore financial datasets and relationships
5. Offer guidance on investment research and analysis

Guidelines:
- Provide accurate, data-driven responses
- Reference specific financial metrics and timeframes
- Explain complex financial concepts clearly
- Suggest follow-up questions for deeper analysis
- Acknowledge limitations and uncertainties
- Use precise financial terminology
- Offer multiple perspectives when appropriate
- Connect current data to historical context"""

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process various types of queries"""
        
        query_type = input_data.get("query_type", "general_query")
        query = input_data.get("query", "")
        
        if query_type == "similar_scenarios":
            return await self._find_similar_scenarios(input_data)
        elif query_type == "company_comparison":
            return await self._compare_companies(input_data)
        elif query_type == "historical_analysis":
            return await self._analyze_historical_data(input_data)
        elif query_type == "market_insights":
            return await self._provide_market_insights(input_data)
        else:
            return await self._answer_general_query(input_data)
    
    async def _answer_general_query(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Answer general financial queries"""
        
        query = input_data.get("query", "")
        context = input_data.get("context", {})
        
        if not query:
            return {
                "response": "Please provide a question about financial data or market analysis.",
                "confidence": 0.0,
                "suggestions": ["Ask about company earnings performance", "Request stock analysis", "Inquire about market trends"]
            }
        
        # Build context for the query
        context_info = ""
        if context:
            context_info = f"\nRelevant Context:\n"
            for key, value in context.items():
                context_info += f"- {key}: {value}\n"
        
        prompt = f"""Answer this financial question with detailed analysis:

Question: {query}
{context_info}

Provide a comprehensive response including:
1. Direct answer to the question
2. Supporting data and evidence
3. Historical context where relevant
4. Key factors to consider
5. Potential implications
6. Suggestions for further analysis
7. Important caveats or limitations

Make your response informative, accurate, and actionable for investment research."""

        try:
            result = await self._call_ollama(prompt, self.get_system_prompt())
            response_text = result.get("response", "")
            
            # Extract structured insights
            confidence = self._assess_response_confidence(response_text, query)
            suggestions = self._generate_follow_up_suggestions(query, response_text)
            key_points = self._extract_key_points(response_text)
            
            return {
                "response": response_text,
                "confidence": confidence,
                "suggestions": suggestions,
                "key_points": key_points,
                "query_type": "general_query",
                "timestamp": datetime.now().isoformat(),
                "processing_time": result.get("total_duration", 0) / 1000000,
            }
            
        except Exception as e:
            return {
                "response": f"I encountered an error processing your question: {str(e)}",
                "confidence": 0.0,
                "suggestions": ["Please try rephrasing your question", "Check if all required data is available"],
                "error": str(e)
            }
    
    async def _find_similar_scenarios(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Find similar historical scenarios"""
        
        symbol = input_data.get("symbol", "")
        scenario_type = input_data.get("scenario_type", "earnings")
        limit = input_data.get("limit", 5)
        current_context = input_data.get("current_context", {})
        
        prompt = f"""Find similar historical scenarios for {symbol} related to {scenario_type}:

Current Context:
"""
        for key, value in current_context.items():
            prompt += f"- {key}: {value}\n"
        
        prompt += f"""

Based on your knowledge of financial markets and {symbol}, identify {limit} similar historical scenarios where:
1. Similar market conditions existed
2. Company fundamentals were comparable  
3. Earnings or events had similar characteristics
4. Market reactions followed similar patterns

For each scenario, provide:
- Date and timeframe
- Brief description of the situation
- Key similarities to current context
- Market outcome and stock performance
- Lessons learned or insights
- Relevance score (1-10)

Focus on scenarios that offer predictive insight for current situation."""

        try:
            result = await self._call_ollama(prompt, self.get_system_prompt())
            response_text = result.get("response", "")
            
            # Parse scenarios from response
            scenarios = self._parse_scenarios(response_text, symbol)
            
            return {
                "scenarios": scenarios,
                "analysis": response_text,
                "symbol": symbol,
                "scenario_type": scenario_type,
                "total_found": len(scenarios),
                "timestamp": datetime.now().isoformat(),
                "processing_time": result.get("total_duration", 0) / 1000000,
            }
            
        except Exception as e:
            return {
                "scenarios": [],
                "analysis": f"Error finding similar scenarios: {str(e)}",
                "error": str(e)
            }
    
    async def _compare_companies(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compare multiple companies"""
        
        symbols = input_data.get("symbols", [])
        comparison_metrics = input_data.get("metrics", ["earnings_performance", "valuation", "growth"])
        
        if len(symbols) < 2:
            return {
                "comparison": "Please provide at least 2 companies to compare",
                "confidence": 0.0
            }
        
        prompt = f"""Compare these companies across key financial metrics:

Companies: {', '.join(symbols)}
Focus Areas: {', '.join(comparison_metrics)}

Based on your knowledge, provide a comprehensive comparison including:
1. Financial performance comparison
2. Valuation metrics analysis
3. Growth prospects assessment
4. Risk profile evaluation
5. Competitive positioning
6. Historical performance patterns
7. Investment thesis for each
8. Relative attractiveness ranking
9. Key differentiating factors
10. Sector context and positioning

Structure your comparison to highlight strengths and weaknesses of each company."""

        try:
            result = await self._call_ollama(prompt, self.get_system_prompt())
            comparison_text = result.get("response", "")
            
            # Extract structured comparison
            rankings = self._extract_rankings(comparison_text, symbols)
            key_differences = self._extract_key_differences(comparison_text)
            
            return {
                "comparison": comparison_text,
                "companies_compared": symbols,
                "rankings": rankings,
                "key_differences": key_differences,
                "metrics_analyzed": comparison_metrics,
                "timestamp": datetime.now().isoformat(),
                "processing_time": result.get("total_duration", 0) / 1000000,
            }
            
        except Exception as e:
            return {
                "comparison": f"Error comparing companies: {str(e)}",
                "error": str(e)
            }
    
    async def _analyze_historical_data(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze historical data patterns"""
        
        symbol = input_data.get("symbol", "")
        time_period = input_data.get("time_period", "2_years")
        analysis_focus = input_data.get("focus", "earnings_patterns")
        
        prompt = f"""Analyze historical data patterns for {symbol} over the past {time_period}:

Focus: {analysis_focus}

Based on your knowledge of {symbol}, analyze:
1. Key historical patterns and trends
2. Seasonal or cyclical behaviors
3. Response to market events
4. Earnings announcement patterns
5. Volatility patterns and drivers
6. Performance relative to benchmarks
7. Key inflection points and catalysts
8. Predictive patterns for future performance
9. Risk factors based on historical data
10. Long-term trajectory and sustainability

Provide actionable insights based on historical analysis."""

        try:
            result = await self._call_ollama(prompt, self.get_system_prompt())
            analysis_text = result.get("response", "")
            
            # Extract patterns and insights
            patterns = self._extract_patterns(analysis_text)
            insights = self._extract_insights(analysis_text)
            
            return {
                "analysis": analysis_text,
                "patterns_identified": patterns,
                "key_insights": insights,
                "symbol": symbol,
                "time_period": time_period,
                "focus": analysis_focus,
                "timestamp": datetime.now().isoformat(),
                "processing_time": result.get("total_duration", 0) / 1000000,
            }
            
        except Exception as e:
            return {
                "analysis": f"Error analyzing historical data: {str(e)}",
                "error": str(e)
            }
    
    async def _provide_market_insights(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Provide market insights and commentary"""
        
        topic = input_data.get("topic", "current_market_conditions")
        sector = input_data.get("sector", "")
        timeframe = input_data.get("timeframe", "current")
        
        prompt = f"""Provide market insights on: {topic}

Sector Focus: {sector if sector else 'Broad Market'}
Timeframe: {timeframe}

Based on your knowledge, provide insights on:
1. Current market conditions and trends
2. Key drivers and catalysts
3. Sector-specific dynamics (if applicable)
4. Risk factors and concerns
5. Opportunities and themes
6. Historical context and precedents
7. Forward-looking considerations
8. Investment implications
9. Key metrics to monitor
10. Potential scenarios and outcomes

Provide actionable market intelligence for investment decision-making."""

        try:
            result = await self._call_ollama(prompt, self.get_system_prompt())
            insights_text = result.get("response", "")
            
            # Extract key themes and implications
            themes = self._extract_themes(insights_text)
            implications = self._extract_implications(insights_text)
            
            return {
                "insights": insights_text,
                "key_themes": themes,
                "implications": implications,
                "topic": topic,
                "sector": sector,
                "timeframe": timeframe,
                "timestamp": datetime.now().isoformat(),
                "processing_time": result.get("total_duration", 0) / 1000000,
            }
            
        except Exception as e:
            return {
                "insights": f"Error providing market insights: {str(e)}",
                "error": str(e)
            }
    
    def _assess_response_confidence(self, response: str, query: str) -> float:
        """Assess confidence in the response"""
        # Simple heuristics for confidence assessment
        confidence = 0.7  # Base confidence
        
        # Increase confidence for specific data mentions
        if any(keyword in response.lower() for keyword in ["data shows", "research indicates", "historically", "according to"]):
            confidence += 0.1
        
        # Decrease confidence for uncertainty language
        if any(keyword in response.lower() for keyword in ["uncertain", "unclear", "might", "possibly", "potentially"]):
            confidence -= 0.1
        
        # Adjust based on response length and detail
        if len(response) > 500:
            confidence += 0.05
        
        return max(0.1, min(0.95, confidence))
    
    def _generate_follow_up_suggestions(self, query: str, response: str) -> List[str]:
        """Generate follow-up question suggestions"""
        suggestions = []
        
        query_lower = query.lower()
        
        if "earnings" in query_lower:
            suggestions = [
                "Show historical earnings surprise patterns",
                "Compare earnings performance to sector peers",
                "Analyze post-earnings stock price movements",
                "Examine earnings guidance accuracy"
            ]
        elif "stock" in query_lower or "price" in query_lower:
            suggestions = [
                "Analyze stock price volatility patterns",
                "Compare performance to market benchmarks",
                "Examine technical chart patterns",
                "Review analyst price targets"
            ]
        elif "company" in query_lower:
            suggestions = [
                "Compare to industry competitors",
                "Analyze financial ratios and metrics",
                "Review recent business developments",
                "Examine insider trading activity"
            ]
        else:
            suggestions = [
                "Get more specific company analysis",
                "Compare multiple companies",
                "Analyze historical trends",
                "Review market implications"
            ]
        
        return suggestions[:4]
    
    def _extract_key_points(self, text: str) -> List[str]:
        """Extract key points from response text"""
        # Simple extraction based on sentence structure
        sentences = text.split('.')
        key_points = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20 and any(keyword in sentence.lower() for keyword in [
                "important", "key", "significant", "notable", "critical", "main"
            ]):
                key_points.append(sentence + ".")
        
        return key_points[:5]
    
    def _parse_scenarios(self, text: str, symbol: str) -> List[Dict[str, Any]]:
        """Parse similar scenarios from response text"""
        scenarios = []
        
        # Simple parsing logic - in production, use more sophisticated NLP
        lines = text.split('\n')
        current_scenario = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Look for date patterns
            if any(month in line.lower() for month in ["january", "february", "march", "april", "may", "june",
                                                      "july", "august", "september", "october", "november", "december"]):
                if current_scenario:
                    scenarios.append(current_scenario)
                current_scenario = {
                    "company_symbol": symbol,
                    "date": line,
                    "similarity_score": 7.5,  # Default
                    "scenario_description": "",
                    "outcome": {},
                    "key_factors": []
                }
            elif current_scenario and line:
                current_scenario["scenario_description"] += line + " "
        
        if current_scenario:
            scenarios.append(current_scenario)
        
        return scenarios[:5]  # Limit to 5 scenarios
    
    def _extract_patterns(self, text: str) -> List[str]:
        """Extract patterns from historical analysis"""
        patterns = []
        pattern_keywords = [
            "seasonal pattern", "cyclical behavior", "recurring trend",
            "consistent pattern", "historical trend", "predictable behavior"
        ]
        
        text_lower = text.lower()
        for keyword in pattern_keywords:
            if keyword in text_lower:
                patterns.append(keyword.title())
        
        return patterns[:6]
    
    def _extract_insights(self, text: str) -> List[str]:
        """Extract key insights from analysis"""
        insights = []
        
        # Look for insight indicators
        sentences = text.split('.')
        for sentence in sentences:
            sentence = sentence.strip()
            if any(indicator in sentence.lower() for indicator in [
                "suggests", "indicates", "reveals", "shows", "demonstrates"
            ]) and len(sentence) > 30:
                insights.append(sentence + ".")
        
        return insights[:5]