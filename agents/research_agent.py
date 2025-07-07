from typing import Dict, List, Any, Optional
import json
from datetime import datetime, timedelta
import re

from agents.base_agent import BaseAgent


class ResearchAgent(BaseAgent):
    def __init__(self):
        super().__init__(model_name="qwen2.5:7b", max_tokens=2000, temperature=0.4)
        
    def get_system_prompt(self) -> str:
        return """You are an expert financial research analyst specializing in gathering and analyzing market intelligence for S&P 500 companies. Your role is to:

1. Analyze financial news, press releases, and market communications
2. Extract key insights from earnings calls and analyst reports
3. Perform sentiment analysis on financial texts
4. Identify market catalysts and risk factors
5. Summarize research findings with actionable insights

Guidelines:
- Focus on factual, data-driven analysis
- Identify both bullish and bearish signals
- Extract specific financial metrics and guidance
- Note management commentary and forward-looking statements
- Assess credibility and relevance of sources
- Provide clear sentiment scores and reasoning
- Highlight time-sensitive information
- Connect research to potential stock price impacts"""

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process research request based on type"""
        
        research_type = input_data.get("research_type", "sentiment_analysis")
        symbol = input_data.get("symbol")
        
        if research_type == "sentiment_analysis":
            return await self._analyze_sentiment(input_data)
        elif research_type == "news_analysis":
            return await self._analyze_news(input_data)
        elif research_type == "earnings_call_analysis":
            return await self._analyze_earnings_call(input_data)
        elif research_type == "analyst_reports":
            return await self._analyze_analyst_reports(input_data)
        elif research_type == "market_intelligence":
            return await self._gather_market_intelligence(input_data)
        else:
            return await self._general_research(input_data)
    
    async def _analyze_sentiment(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze sentiment of financial text"""
        
        text = input_data.get("text", "")
        symbol = input_data.get("symbol", "")
        source = input_data.get("source", "")
        
        if not text:
            return {
                "sentiment": "neutral",
                "confidence": 0.0,
                "analysis": "No text provided for sentiment analysis",
                "scores": {"positive": 0.0, "negative": 0.0, "neutral": 1.0}
            }
        
        prompt = f"""Analyze the sentiment of this financial text related to {symbol}:

Source: {source}
Text: "{text}"

Provide detailed sentiment analysis including:
1. Overall sentiment (bullish/bearish/neutral)
2. Confidence level (0-100%)
3. Key positive factors mentioned
4. Key negative factors mentioned
5. Specific sentiment scores (positive, negative, neutral percentages)
6. Impact assessment on stock price
7. Time sensitivity of the information

Focus on financial implications and market-moving information."""

        try:
            result = await self._call_ollama(prompt, self.get_system_prompt())
            analysis_text = result.get("response", "")
            
            # Extract sentiment scores using pattern matching
            sentiment_scores = self._extract_sentiment_scores(analysis_text)
            overall_sentiment = self._determine_overall_sentiment(sentiment_scores)
            confidence = self._extract_confidence(analysis_text)
            
            # Extract key factors
            positive_factors = self._extract_factors(analysis_text, "positive")
            negative_factors = self._extract_factors(analysis_text, "negative")
            
            return {
                "sentiment": overall_sentiment,
                "confidence": confidence,
                "analysis": analysis_text,
                "scores": sentiment_scores,
                "positive_factors": positive_factors,
                "negative_factors": negative_factors,
                "symbol": symbol,
                "source": source,
                "timestamp": datetime.now().isoformat(),
                "processing_time": result.get("total_duration", 0) / 1000000,
            }
            
        except Exception as e:
            return {
                "sentiment": "neutral",
                "confidence": 0.0,
                "analysis": f"Error in sentiment analysis: {str(e)}",
                "scores": {"positive": 0.0, "negative": 0.0, "neutral": 1.0},
                "error": str(e)
            }
    
    async def _analyze_news(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze financial news articles"""
        
        articles = input_data.get("articles", [])
        symbol = input_data.get("symbol", "")
        time_horizon = input_data.get("time_horizon", "1week")
        
        if not articles:
            return {
                "analysis": "No news articles provided",
                "sentiment_summary": "neutral",
                "key_themes": [],
                "market_impact": "low"
            }
        
        # Combine articles for analysis
        combined_text = ""
        for article in articles[:10]:  # Limit to 10 most recent
            combined_text += f"Headline: {article.get('headline', '')}\n"
            combined_text += f"Content: {article.get('content', '')[:500]}...\n\n"
        
        prompt = f"""Analyze the following recent news articles about {symbol}:

Time Horizon: {time_horizon}
Number of Articles: {len(articles)}

News Content:
{combined_text}

Provide comprehensive news analysis including:
1. Overall sentiment trend across articles
2. Key themes and topics mentioned
3. Market-moving events or announcements
4. Analyst opinions and price target changes
5. Regulatory or competitive developments
6. Management guidance or corporate actions
7. Expected market impact (high/medium/low)
8. Key catalysts identified
9. Risk factors highlighted
10. Summary and investment implications

Focus on actionable insights for stock performance prediction."""

        try:
            result = await self._call_ollama(prompt, self.get_system_prompt())
            analysis_text = result.get("response", "")
            
            # Extract structured insights
            sentiment_summary = self._extract_news_sentiment(analysis_text)
            key_themes = self._extract_themes(analysis_text)
            market_impact = self._extract_market_impact(analysis_text)
            catalysts = self._extract_catalysts(analysis_text)
            
            return {
                "analysis": analysis_text,
                "sentiment_summary": sentiment_summary,
                "key_themes": key_themes,
                "market_impact": market_impact,
                "catalysts": catalysts,
                "articles_analyzed": len(articles),
                "symbol": symbol,
                "time_horizon": time_horizon,
                "timestamp": datetime.now().isoformat(),
                "processing_time": result.get("total_duration", 0) / 1000000,
            }
            
        except Exception as e:
            return {
                "analysis": f"Error in news analysis: {str(e)}",
                "sentiment_summary": "neutral",
                "key_themes": [],
                "market_impact": "unknown",
                "error": str(e)
            }
    
    async def _analyze_earnings_call(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze earnings call transcript"""
        
        transcript = input_data.get("transcript", "")
        symbol = input_data.get("symbol", "")
        quarter = input_data.get("quarter", "")
        year = input_data.get("year", "")
        
        if not transcript:
            return {
                "analysis": "No earnings call transcript provided",
                "management_tone": "neutral",
                "key_guidance": [],
                "outlook": "neutral"
            }
        
        # Truncate transcript if too long
        if len(transcript) > 5000:
            transcript = transcript[:5000] + "..."
        
        prompt = f"""Analyze this earnings call transcript for {symbol} - {quarter} {year}:

Transcript:
{transcript}

Provide detailed earnings call analysis including:
1. Management tone and confidence level
2. Key financial guidance and metrics mentioned
3. Forward-looking statements and outlook
4. Management commentary on business segments
5. Q&A highlights and analyst concerns
6. Positive developments and growth drivers
7. Challenges and risk factors discussed
8. Comparison to previous guidance
9. Market reaction indicators
10. Investment thesis implications

Focus on extracting actionable insights that could impact stock performance."""

        try:
            result = await self._call_ollama(prompt, self.get_system_prompt())
            analysis_text = result.get("response", "")
            
            # Extract structured insights
            management_tone = self._extract_management_tone(analysis_text)
            key_guidance = self._extract_guidance(analysis_text)
            outlook = self._extract_outlook(analysis_text)
            risk_factors = self._extract_risk_factors(analysis_text)
            
            return {
                "analysis": analysis_text,
                "management_tone": management_tone,
                "key_guidance": key_guidance,
                "outlook": outlook,
                "risk_factors": risk_factors,
                "symbol": symbol,
                "quarter": quarter,
                "year": year,
                "timestamp": datetime.now().isoformat(),
                "processing_time": result.get("total_duration", 0) / 1000000,
            }
            
        except Exception as e:
            return {
                "analysis": f"Error in earnings call analysis: {str(e)}",
                "management_tone": "neutral",
                "key_guidance": [],
                "outlook": "neutral",
                "error": str(e)
            }
    
    async def _gather_market_intelligence(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Gather comprehensive market intelligence"""
        
        symbol = input_data.get("symbol", "")
        focus_areas = input_data.get("focus_areas", ["earnings", "guidance", "sentiment"])
        
        prompt = f"""Provide comprehensive market intelligence summary for {symbol} focusing on:
{', '.join(focus_areas)}

Based on your knowledge, analyze:
1. Recent company developments and announcements
2. Industry trends affecting the company
3. Competitive landscape changes
4. Regulatory environment impacts
5. Macroeconomic factors
6. Seasonal business patterns
7. Key upcoming catalysts
8. Analyst consensus and recent changes
9. Technical trading patterns
10. Risk assessment

Provide actionable intelligence for investment decision-making."""

        try:
            result = await self._call_ollama(prompt, self.get_system_prompt())
            analysis_text = result.get("response", "")
            
            return {
                "intelligence": analysis_text,
                "symbol": symbol,
                "focus_areas": focus_areas,
                "timestamp": datetime.now().isoformat(),
                "processing_time": result.get("total_duration", 0) / 1000000,
            }
            
        except Exception as e:
            return {
                "intelligence": f"Error gathering market intelligence: {str(e)}",
                "error": str(e)
            }
    
    def _extract_sentiment_scores(self, text: str) -> Dict[str, float]:
        """Extract sentiment scores from analysis text"""
        # Simple pattern matching for sentiment scores
        positive_match = re.search(r'positive[:\s]*(\d+(?:\.\d+)?)', text.lower())
        negative_match = re.search(r'negative[:\s]*(\d+(?:\.\d+)?)', text.lower())
        neutral_match = re.search(r'neutral[:\s]*(\d+(?:\.\d+)?)', text.lower())
        
        positive = float(positive_match.group(1)) / 100 if positive_match else 0.33
        negative = float(negative_match.group(1)) / 100 if negative_match else 0.33
        neutral = float(neutral_match.group(1)) / 100 if neutral_match else 0.34
        
        # Normalize to sum to 1
        total = positive + negative + neutral
        if total > 0:
            positive /= total
            negative /= total
            neutral /= total
        
        return {"positive": positive, "negative": negative, "neutral": neutral}
    
    def _determine_overall_sentiment(self, scores: Dict[str, float]) -> str:
        """Determine overall sentiment from scores"""
        if scores["positive"] > scores["negative"] and scores["positive"] > scores["neutral"]:
            return "bullish"
        elif scores["negative"] > scores["positive"] and scores["negative"] > scores["neutral"]:
            return "bearish"
        else:
            return "neutral"
    
    def _extract_confidence(self, text: str) -> float:
        """Extract confidence level from text"""
        confidence_match = re.search(r'confidence[:\s]*(\d+(?:\.\d+)?)', text.lower())
        if confidence_match:
            return float(confidence_match.group(1)) / 100 if float(confidence_match.group(1)) > 1 else float(confidence_match.group(1))
        
        # Default confidence based on text length and detail
        return min(0.8, len(text) / 1000)
    
    def _extract_factors(self, text: str, factor_type: str) -> List[str]:
        """Extract positive or negative factors from text"""
        factors = []
        
        # Simple pattern matching for factors
        if factor_type == "positive":
            patterns = [r'positive factors?[:\s]*([^.]+)', r'bullish[:\s]*([^.]+)', r'strengths?[:\s]*([^.]+)']
        else:
            patterns = [r'negative factors?[:\s]*([^.]+)', r'bearish[:\s]*([^.]+)', r'weaknesses?[:\s]*([^.]+)']
        
        for pattern in patterns:
            matches = re.findall(pattern, text.lower())
            factors.extend(matches)
        
        return factors[:5]  # Limit to 5 factors
    
    def _extract_themes(self, text: str) -> List[str]:
        """Extract key themes from news analysis"""
        # Simple keyword extraction
        themes = []
        theme_keywords = [
            "earnings", "revenue", "guidance", "margins", "growth", "acquisition",
            "partnership", "regulation", "competition", "innovation", "expansion"
        ]
        
        text_lower = text.lower()
        for keyword in theme_keywords:
            if keyword in text_lower:
                themes.append(keyword.title())
        
        return themes[:7]  # Limit to 7 themes
    
    def _extract_market_impact(self, text: str) -> str:
        """Extract market impact assessment"""
        text_lower = text.lower()
        if "high impact" in text_lower or "significant" in text_lower:
            return "high"
        elif "medium impact" in text_lower or "moderate" in text_lower:
            return "medium"
        elif "low impact" in text_lower or "minimal" in text_lower:
            return "low"
        else:
            return "medium"  # Default
    
    async def _general_research(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform general research analysis"""
        return await self._gather_market_intelligence(input_data)