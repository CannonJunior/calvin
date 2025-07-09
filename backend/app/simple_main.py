#!/usr/bin/env python3
"""
Minimal FastAPI server for testing
"""
from fastapi import FastAPI
import uvicorn

# Create the most basic FastAPI app possible
app = FastAPI(title="Calvin API Test", version="0.1.0")

@app.get("/")
async def root():
    return {"message": "Calvin API is running", "status": "ok"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/api/v1/companies")
async def companies(limit: int = 5):
    data = [
        {"symbol": "AAPL", "name": "Apple Inc."},
        {"symbol": "MSFT", "name": "Microsoft Corp."},
        {"symbol": "GOOGL", "name": "Alphabet Inc."},
        {"symbol": "AMZN", "name": "Amazon Inc."},
        {"symbol": "TSLA", "name": "Tesla Inc."},
    ]
    return data[:limit]

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)