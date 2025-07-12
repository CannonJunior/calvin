# Copyright 2025 CannonJunior
  
# This file is part of mcp_experiments, and is released under the "MIT License Agreement".
# Please see the LICENSE.md file that should have been included as part of this package.
# Enhanced MCP Sentiment Analysis Server for financial text analysis
# Usage: uv run sentiment_analysis_server.py

from fastmcp import FastMCP
from textblob import TextBlob
import json
import re
from datetime import datetime
from typing import Dict, Any, List, Optional

mcp = FastMCP("Sentiment Analysis Server")

# Financial keywords for enhanced analysis
POSITIVE_FINANCIAL_KEYWORDS = [
    "beat", "exceed", "growth", "profit", "revenue", "strong", "outperform",
    "bullish", "upgrade", "buy", "positive", "gains", "rally", "surge"
]

NEGATIVE_FINANCIAL_KEYWORDS = [
    "miss", "decline", "loss", "weak", "underperform", "bearish", "downgrade",
    "sell", "negative", "drop", "fall", "crash", "concern", "risk"
]

@mcp.tool()
async def analyze_sentiment(text: str) -> Dict[str, Any]:
    """Analyze sentiment of text using TextBlob with financial context"""
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    subjectivity = blob.sentiment.subjectivity
    
    # Enhanced sentiment classification
    if polarity > 0.3:
        sentiment = "very positive"
    elif polarity > 0.1:
        sentiment = "positive"
    elif polarity > -0.1:
        sentiment = "neutral"
    elif polarity > -0.3:
        sentiment = "negative"
    else:
        sentiment = "very negative"
    
    # Financial keyword analysis
    text_lower = text.lower()
    positive_matches = [kw for kw in POSITIVE_FINANCIAL_KEYWORDS if kw in text_lower]
    negative_matches = [kw for kw in NEGATIVE_FINANCIAL_KEYWORDS if kw in text_lower]
    
    # Adjust confidence based on financial keywords
    financial_boost = 0
    if positive_matches and polarity > 0:
        financial_boost = 0.2
    elif negative_matches and polarity < 0:
        financial_boost = 0.2
    
    confidence = min(abs(polarity) + financial_boost, 1.0)
    
    return {
        "sentiment": sentiment,
        "polarity": round(polarity, 3),
        "subjectivity": round(subjectivity, 3),
        "confidence": round(confidence, 3),
        "financial_keywords": {
            "positive": positive_matches,
            "negative": negative_matches
        },
        "analysis_timestamp": datetime.now().isoformat()
    }

@mcp.tool()
async def analyze_earnings_sentiment(
    earnings_text: str,
    context: Optional[str] = "earnings_call"
) -> Dict[str, Any]:
    """Specialized sentiment analysis for earnings-related text"""
    
    # Base sentiment analysis
    base_analysis = await analyze_sentiment(earnings_text)
    
    # Earnings-specific keywords
    earnings_positive = ["guidance raise", "beat expectations", "strong quarter", 
                        "margin expansion", "record revenue", "growth outlook"]
    earnings_negative = ["guidance cut", "miss expectations", "weak quarter",
                        "margin compression", "revenue decline", "uncertainty"]
    
    text_lower = earnings_text.lower()
    
    # Count earnings-specific mentions
    positive_earnings = sum(1 for phrase in earnings_positive if phrase in text_lower)
    negative_earnings = sum(1 for phrase in earnings_negative if phrase in text_lower)
    
    # Calculate earnings-specific sentiment score
    earnings_score = positive_earnings - negative_earnings
    
    # Determine earnings sentiment category
    if earnings_score > 1:
        earnings_sentiment = "very bullish"
    elif earnings_score > 0:
        earnings_sentiment = "bullish"
    elif earnings_score < -1:
        earnings_sentiment = "very bearish"
    elif earnings_score < 0:
        earnings_sentiment = "bearish"
    else:
        earnings_sentiment = "neutral"
    
    return {
        "general_sentiment": base_analysis,
        "earnings_sentiment": earnings_sentiment,
        "earnings_score": earnings_score,
        "context": context,
        "earnings_indicators": {
            "positive_mentions": positive_earnings,
            "negative_mentions": negative_earnings,
            "key_phrases_found": [phrase for phrase in earnings_positive + earnings_negative 
                                 if phrase in text_lower]
        }
    }

@mcp.tool()
async def batch_sentiment_analysis(
    texts: List[str],
    labels: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Analyze sentiment for multiple texts in batch"""
    
    if labels and len(labels) != len(texts):
        return {"error": "Labels list must match texts list length"}
    
    results = []
    
    for i, text in enumerate(texts):
        analysis = await analyze_sentiment(text)
        
        result = {
            "index": i,
            "text_preview": text[:100] + "..." if len(text) > 100 else text,
            "analysis": analysis
        }
        
        if labels:
            result["label"] = labels[i]
            
        results.append(result)
    
    # Calculate aggregate statistics
    polarities = [r["analysis"]["polarity"] for r in results]
    avg_polarity = sum(polarities) / len(polarities) if polarities else 0
    
    sentiment_counts = {}
    for result in results:
        sentiment = result["analysis"]["sentiment"]
        sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
    
    return {
        "batch_results": results,
        "aggregate_stats": {
            "total_texts": len(texts),
            "average_polarity": round(avg_polarity, 3),
            "sentiment_distribution": sentiment_counts
        },
        "processed_at": datetime.now().isoformat()
    }

@mcp.tool()
async def sentiment_trend_analysis(
    time_series_texts: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Analyze sentiment trends over time"""
    
    if not time_series_texts:
        return {"error": "No time series data provided"}
    
    # Validate input format
    required_fields = ["timestamp", "text"]
    for item in time_series_texts:
        if not all(field in item for field in required_fields):
            return {"error": f"Each item must have fields: {required_fields}"}
    
    # Sort by timestamp
    sorted_data = sorted(time_series_texts, key=lambda x: x["timestamp"])
    
    trend_analysis = []
    
    for item in sorted_data:
        sentiment_result = await analyze_sentiment(item["text"])
        
        trend_analysis.append({
            "timestamp": item["timestamp"],
            "text_preview": item["text"][:50] + "..." if len(item["text"]) > 50 else item["text"],
            "sentiment": sentiment_result["sentiment"],
            "polarity": sentiment_result["polarity"],
            "confidence": sentiment_result["confidence"]
        })
    
    # Calculate trend metrics
    polarities = [item["polarity"] for item in trend_analysis]
    
    if len(polarities) > 1:
        # Simple trend calculation
        trend_direction = "improving" if polarities[-1] > polarities[0] else "declining"
        volatility = max(polarities) - min(polarities)
    else:
        trend_direction = "insufficient_data"
        volatility = 0
    
    return {
        "trend_data": trend_analysis,
        "trend_metrics": {
            "overall_direction": trend_direction,
            "volatility": round(volatility, 3),
            "start_polarity": polarities[0] if polarities else 0,
            "end_polarity": polarities[-1] if polarities else 0,
            "average_polarity": round(sum(polarities) / len(polarities), 3) if polarities else 0
        }
    }

@mcp.tool()
async def extract_key_sentiments(
    text: str,
    min_sentence_length: int = 10
) -> Dict[str, Any]:
    """Extract and analyze sentiment of key sentences from text"""
    
    # Split into sentences
    blob = TextBlob(text)
    sentences = [str(sentence).strip() for sentence in blob.sentences 
                if len(str(sentence).strip()) >= min_sentence_length]
    
    sentence_sentiments = []
    
    for sentence in sentences:
        sentiment_result = await analyze_sentiment(sentence)
        
        sentence_sentiments.append({
            "sentence": sentence,
            "sentiment": sentiment_result["sentiment"],
            "polarity": sentiment_result["polarity"],
            "confidence": sentiment_result["confidence"]
        })
    
    # Sort by absolute polarity (most extreme sentiments first)
    sorted_sentiments = sorted(sentence_sentiments, 
                              key=lambda x: abs(x["polarity"]), 
                              reverse=True)
    
    # Extract most positive and negative sentences
    most_positive = [s for s in sorted_sentiments if s["polarity"] > 0][:3]
    most_negative = [s for s in sorted_sentiments if s["polarity"] < 0][:3]
    
    return {
        "all_sentences": sentence_sentiments,
        "key_sentiments": {
            "most_positive": most_positive,
            "most_negative": most_negative,
            "most_extreme": sorted_sentiments[:5]
        },
        "summary": {
            "total_sentences": len(sentences),
            "positive_sentences": len([s for s in sentence_sentiments if s["polarity"] > 0]),
            "negative_sentences": len([s for s in sentence_sentiments if s["polarity"] < 0]),
            "neutral_sentences": len([s for s in sentence_sentiments if abs(s["polarity"]) <= 0.1])
        }
    }

@mcp.resource("sentiment://financial-keywords")
async def financial_keywords_resource() -> str:
    """Resource providing financial sentiment keywords"""
    keywords_data = {
        "positive_keywords": POSITIVE_FINANCIAL_KEYWORDS,
        "negative_keywords": NEGATIVE_FINANCIAL_KEYWORDS,
        "usage": "These keywords enhance sentiment analysis for financial text"
    }
    return json.dumps(keywords_data, indent=2)

@mcp.prompt("sentiment-analysis")
async def sentiment_analysis_prompt(text: str = "") -> str:
    """Generate prompt for detailed sentiment analysis"""
    return f"""Analyze the sentiment of the following text with focus on financial implications:

Text: "{text}"

Provide analysis including:
1. Overall sentiment (positive/negative/neutral)
2. Confidence level
3. Key emotional indicators
4. Financial market implications
5. Potential impact on stock performance
6. Risk factors mentioned
7. Sentiment score (-10 to +10)

Consider financial terminology, market context, and investor psychology in your analysis."""

if __name__ == "__main__":
    mcp.run()
