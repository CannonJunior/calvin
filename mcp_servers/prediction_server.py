#!/usr/bin/env python3
"""
MCP Server for Stock Prediction Engine
Handles next-day performance predictions after earnings announcements
"""
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any
import random
from fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP("Stock Prediction Server")

# Base paths for data storage
ASSETS_DIR = Path(__file__).parent.parent / "assets"
PREDICTIONS_DIR = ASSETS_DIR / "predictions"

def ensure_directories():
    """Ensure required directories exist"""
    PREDICTIONS_DIR.mkdir(parents=True, exist_ok=True)

@mcp.tool()
async def predict_next_day_performance(
    symbol: str,
    earnings_data: Dict[str, Any],
    market_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Predict next-day stock performance after earnings announcement
    
    Args:
        symbol: Company ticker symbol
        earnings_data: Dictionary with earnings results and surprise data
        market_context: Optional market conditions context
    
    Returns:
        Dictionary with prediction data
    """
    ensure_directories()
    
    symbol = symbol.upper()
    
    # Extract key features for prediction
    eps_surprise_percent = earnings_data.get('eps_surprise_percent', 0)
    revenue_surprise_percent = earnings_data.get('revenue_surprise_percent', 0)
    surprise_category = earnings_data.get('surprise_category', 'Meet')
    
    # Simple prediction model (in production, this would use ML)
    base_movement = 0
    confidence = 0.5
    
    # EPS surprise impact
    if eps_surprise_percent > 10:
        base_movement += 3.5
        confidence += 0.2
    elif eps_surprise_percent > 5:
        base_movement += 2.0
        confidence += 0.15
    elif eps_surprise_percent > 0:
        base_movement += 0.8
        confidence += 0.1
    elif eps_surprise_percent < -10:
        base_movement -= 4.0
        confidence += 0.15
    elif eps_surprise_percent < -5:
        base_movement -= 2.5
        confidence += 0.1
    else:
        base_movement -= 0.5
        confidence += 0.05
    
    # Revenue surprise impact
    if revenue_surprise_percent > 5:
        base_movement += 1.0
        confidence += 0.1
    elif revenue_surprise_percent < -5:
        base_movement -= 1.5
        confidence += 0.1
    
    # Market context adjustments
    if market_context:
        market_trend = market_context.get('trend', 'neutral')
        if market_trend == 'bullish':
            base_movement *= 1.2
        elif market_trend == 'bearish':
            base_movement *= 0.8
    
    # Add some randomness for realism
    noise = random.uniform(-0.5, 0.5)
    predicted_return = base_movement + noise
    
    # Confidence adjustments
    confidence = min(confidence, 0.95)  # Cap at 95%
    confidence = max(confidence, 0.3)   # Floor at 30%
    
    # Prediction categories
    if predicted_return > 2:
        direction = "Strong Positive"
        magnitude = "High"
    elif predicted_return > 0.5:
        direction = "Positive"
        magnitude = "Medium"
    elif predicted_return > -0.5:
        direction = "Neutral"
        magnitude = "Low"
    elif predicted_return > -2:
        direction = "Negative"
        magnitude = "Medium"
    else:
        direction = "Strong Negative"
        magnitude = "High"
    
    prediction = {
        "symbol": symbol,
        "prediction_date": datetime.now().isoformat(),
        "earnings_date": earnings_data.get('earnings_date'),
        "predicted_return_percent": round(predicted_return, 2),
        "confidence_score": round(confidence, 3),
        "direction": direction,
        "magnitude": magnitude,
        "model_version": "1.0",
        "features_used": {
            "eps_surprise_percent": eps_surprise_percent,
            "revenue_surprise_percent": revenue_surprise_percent,
            "surprise_category": surprise_category,
            "market_context": market_context
        }
    }
    
    # Save prediction
    await save_prediction(prediction)
    
    return prediction

@mcp.tool()
async def save_prediction(prediction_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Save prediction data for future analysis
    
    Args:
        prediction_data: Dictionary containing prediction information
    
    Returns:
        Success/error message
    """
    ensure_directories()
    
    if 'symbol' not in prediction_data:
        return {"error": "Symbol is required"}
    
    symbol = prediction_data['symbol'].upper()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prediction_file = PREDICTIONS_DIR / f"{symbol}_{timestamp}_prediction.json"
    
    try:
        with open(prediction_file, 'w') as f:
            json.dump(prediction_data, f, indent=2)
        
        return {
            "success": True,
            "message": f"Prediction for {symbol} saved successfully",
            "file": str(prediction_file)
        }
    except Exception as e:
        return {"error": f"Failed to save prediction: {str(e)}"}

@mcp.tool()
async def get_prediction_history(
    symbol: str,
    days_back: int = 30
) -> Dict[str, Any]:
    """
    Get historical predictions for a company
    
    Args:
        symbol: Company ticker symbol
        days_back: Number of days of history to return
    
    Returns:
        Dictionary with historical predictions
    """
    ensure_directories()
    
    symbol = symbol.upper()
    cutoff_date = datetime.now() - timedelta(days=days_back)
    
    predictions = []
    
    for prediction_file in PREDICTIONS_DIR.glob(f"{symbol}_*_prediction.json"):
        try:
            # Extract date from filename
            date_str = prediction_file.stem.split('_')[1]
            file_date = datetime.strptime(date_str, "%Y%m%d")
            
            if file_date >= cutoff_date:
                with open(prediction_file, 'r') as f:
                    prediction_data = json.load(f)
                predictions.append(prediction_data)
                
        except (ValueError, json.JSONDecodeError, FileNotFoundError):
            continue
    
    # Sort by prediction date
    predictions.sort(key=lambda x: x.get('prediction_date', ''), reverse=True)
    
    return {
        "symbol": symbol,
        "predictions": predictions,
        "total_predictions": len(predictions),
        "days_back": days_back
    }

@mcp.tool()
async def analyze_prediction_accuracy(
    symbol: str,
    actual_results: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Analyze accuracy of past predictions against actual results
    
    Args:
        symbol: Company ticker symbol
        actual_results: List of actual stock performance data
    
    Returns:
        Dictionary with accuracy analysis
    """
    history = await get_prediction_history(symbol, days_back=365)
    predictions = history.get('predictions', [])
    
    if not predictions or not actual_results:
        return {"error": "Insufficient data for accuracy analysis"}
    
    matches = []
    
    # Match predictions with actual results
    for prediction in predictions:
        pred_date = prediction.get('earnings_date')
        if not pred_date:
            continue
            
        for actual in actual_results:
            actual_date = actual.get('date')
            if pred_date == actual_date:
                predicted_return = prediction.get('predicted_return_percent', 0)
                actual_return = actual.get('next_day_return', 0)
                error = abs(predicted_return - actual_return)
                
                matches.append({
                    "date": pred_date,
                    "predicted": predicted_return,
                    "actual": actual_return,
                    "error": round(error, 2),
                    "confidence": prediction.get('confidence_score', 0)
                })
                break
    
    if not matches:
        return {"error": "No matching predictions and actual results found"}
    
    # Calculate accuracy metrics
    total_error = sum(match['error'] for match in matches)
    mean_absolute_error = total_error / len(matches)
    
    # Direction accuracy
    correct_direction = 0
    for match in matches:
        pred_sign = 1 if match['predicted'] > 0 else -1
        actual_sign = 1 if match['actual'] > 0 else -1
        if pred_sign == actual_sign:
            correct_direction += 1
    
    direction_accuracy = correct_direction / len(matches)
    
    return {
        "symbol": symbol,
        "total_predictions_analyzed": len(matches),
        "mean_absolute_error": round(mean_absolute_error, 2),
        "direction_accuracy_percent": round(direction_accuracy * 100, 1),
        "matches": matches[-10:]  # Last 10 matches for review
    }

@mcp.tool()
async def get_batch_predictions(
    earnings_calendar: List[Dict[str, Any]],
    market_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate predictions for multiple companies with upcoming earnings
    
    Args:
        earnings_calendar: List of upcoming earnings announcements
        market_context: Optional market conditions context
    
    Returns:
        Dictionary with batch predictions
    """
    batch_predictions = []
    
    for earnings in earnings_calendar:
        if 'symbol' in earnings:
            try:
                prediction = await predict_next_day_performance(
                    earnings['symbol'],
                    earnings,
                    market_context
                )
                batch_predictions.append(prediction)
            except Exception as e:
                batch_predictions.append({
                    "symbol": earnings.get('symbol'),
                    "error": f"Prediction failed: {str(e)}"
                })
    
    return {
        "batch_predictions": batch_predictions,
        "total_processed": len(batch_predictions),
        "market_context": market_context,
        "generated_at": datetime.now().isoformat()
    }

@mcp.tool()
async def get_top_predictions(
    confidence_threshold: float = 0.7,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Get top recent predictions above confidence threshold
    
    Args:
        confidence_threshold: Minimum confidence score
        limit: Maximum number of predictions to return
    
    Returns:
        Dictionary with top predictions
    """
    ensure_directories()
    
    all_predictions = []
    cutoff_date = datetime.now() - timedelta(days=7)  # Last week
    
    for prediction_file in PREDICTIONS_DIR.glob("*_prediction.json"):
        try:
            # Extract date from filename
            date_str = prediction_file.stem.split('_')[1]
            file_date = datetime.strptime(date_str, "%Y%m%d")
            
            if file_date >= cutoff_date:
                with open(prediction_file, 'r') as f:
                    prediction_data = json.load(f)
                    
                confidence = prediction_data.get('confidence_score', 0)
                if confidence >= confidence_threshold:
                    all_predictions.append(prediction_data)
                    
        except (ValueError, json.JSONDecodeError, FileNotFoundError):
            continue
    
    # Sort by confidence score descending
    all_predictions.sort(key=lambda x: x.get('confidence_score', 0), reverse=True)
    
    return {
        "top_predictions": all_predictions[:limit],
        "confidence_threshold": confidence_threshold,
        "total_found": len(all_predictions)
    }

@mcp.resource("predictions://recent")
async def recent_predictions_resource() -> str:
    """Resource providing recent high-confidence predictions"""
    recent_data = await get_top_predictions(confidence_threshold=0.6, limit=20)
    return json.dumps(recent_data, indent=2)

@mcp.resource("predictions://summary")
async def predictions_summary_resource() -> str:
    """Resource providing prediction summary statistics"""
    # Get all recent predictions for summary
    all_recent = await get_top_predictions(confidence_threshold=0.0, limit=100)
    predictions = all_recent.get('top_predictions', [])
    
    if not predictions:
        summary = {"message": "No recent predictions available"}
    else:
        # Calculate summary stats
        avg_confidence = sum(p.get('confidence_score', 0) for p in predictions) / len(predictions)
        direction_counts = {}
        
        for p in predictions:
            direction = p.get('direction', 'Unknown')
            direction_counts[direction] = direction_counts.get(direction, 0) + 1
        
        summary = {
            "total_predictions": len(predictions),
            "average_confidence": round(avg_confidence, 3),
            "direction_distribution": direction_counts,
            "last_updated": datetime.now().isoformat()
        }
    
    return json.dumps(summary, indent=2)

if __name__ == "__main__":
    # Run the MCP server
    mcp.run()