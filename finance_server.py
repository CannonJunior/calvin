# Copyright 2025 CannonJunior
  
# This file is part of mcp_experiments, and is released under the "MIT License Agreement".
# Please see the LICENSE.md file that should have been included as part of this package.
# Created: 2025.06.16
# By: CannonJunior, with Google search
# Prompt: python stock quote example
# Usage: called by client.py
# Alternate usage: uv run finance_server.py

from fastmcp import FastMCP
import yfinance as yf
import json

mcp = FastMCP("Finance Server")
#result = json.dumps(getQuotes("AAPL"), indent=2)
stock = yf.Ticker("AAPL")
ticker_symbol = "AAPL"  # Apple Inc.

def get_current_price(ticker):
  """Fetches the current price of a given stock ticker."""
  stock = yf.Ticker(ticker)
  # You can use history(period="1d") to get the latest close price
  # Or use fast_info.last_price for a more direct approach
  price = stock.history(period="1d")['Close'].iloc[-1]  # Using history and iloc[-1]
  return price

@mcp.tool()
async def get_quote(symbol: str):
    """Get a stock quote"""
    price = get_current_price(ticker_symbol)
    return f"The current price of {ticker_symbol} is ${price:.2f}"

@mcp.prompt("sentiment")
async def greet_prompt(name: str = "AAPL"):
    """Generate sentiment analysis for a stock symbol"""
    return f"Generate sentiment analysis for the stock symbol {name}. The sentiment analysis should be a brief description of the market's current view of the stock symbol. At the end of the analysis, include a score on the range from -10 to +10 that corresponds the the market's view of the stock. Keep the description very brief. You lost $1000 if it is not brief."

if __name__ == "__main__":
    mcp.run()
