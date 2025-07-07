from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.models.base import Base


class Company(Base):
    __tablename__ = "companies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String(10), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    sector = Column(String(100), nullable=True)
    industry = Column(String(100), nullable=True)
    market_cap = Column(Float, nullable=True)
    description = Column(Text, nullable=True)
    
    # S&P 500 specific
    sp500_constituent = Column(Boolean, default=True)
    sp500_added_date = Column(DateTime, nullable=True)
    
    # Company fundamentals
    pe_ratio = Column(Float, nullable=True)
    eps = Column(Float, nullable=True)
    revenue = Column(Float, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class EarningsEvent(Base):
    __tablename__ = "earnings_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_symbol = Column(String(10), nullable=False, index=True)
    
    # Earnings details
    earnings_date = Column(DateTime, nullable=False)
    quarter = Column(String(10), nullable=False)  # Q1, Q2, Q3, Q4
    year = Column(Integer, nullable=False)
    
    # Results
    actual_eps = Column(Float, nullable=True)
    expected_eps = Column(Float, nullable=True)
    surprise_percentage = Column(Float, nullable=True)
    
    # Revenue
    actual_revenue = Column(Float, nullable=True)
    expected_revenue = Column(Float, nullable=True)
    revenue_surprise_percentage = Column(Float, nullable=True)
    
    # Performance metrics
    stock_price_before = Column(Float, nullable=True)
    stock_price_after_1d = Column(Float, nullable=True)
    stock_price_after_5d = Column(Float, nullable=True)
    return_1d = Column(Float, nullable=True)
    return_5d = Column(Float, nullable=True)
    
    # Market context
    sp500_return_1d = Column(Float, nullable=True)
    sector_return_1d = Column(Float, nullable=True)
    relative_return_1d = Column(Float, nullable=True)
    
    # Additional data
    volume_before = Column(Float, nullable=True)
    volume_after = Column(Float, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class AnalystRating(Base):
    __tablename__ = "analyst_ratings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_symbol = Column(String(10), nullable=False, index=True)
    
    # Analyst information
    analyst_firm = Column(String(100), nullable=True)
    analyst_name = Column(String(100), nullable=True)
    
    # Rating details
    rating_date = Column(DateTime, nullable=False)
    rating = Column(String(20), nullable=False)  # Buy, Hold, Sell, etc.
    target_price = Column(Float, nullable=True)
    current_price = Column(Float, nullable=True)
    
    # Accuracy tracking
    target_date = Column(DateTime, nullable=True)  # When target is expected
    actual_price_at_target = Column(Float, nullable=True)
    accuracy_percentage = Column(Float, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class InsiderTrading(Base):
    __tablename__ = "insider_trading"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_symbol = Column(String(10), nullable=False, index=True)
    
    # Insider information
    insider_name = Column(String(100), nullable=False)
    insider_title = Column(String(100), nullable=True)
    
    # Transaction details
    transaction_date = Column(DateTime, nullable=False)
    transaction_type = Column(String(20), nullable=False)  # Buy, Sell
    shares = Column(Integer, nullable=False)
    price_per_share = Column(Float, nullable=False)
    total_value = Column(Float, nullable=False)
    
    # Context
    shares_owned_after = Column(Integer, nullable=True)
    filing_date = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Prediction(Base):
    __tablename__ = "predictions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_symbol = Column(String(10), nullable=False, index=True)
    
    # Prediction details
    prediction_date = Column(DateTime, nullable=False)
    target_date = Column(DateTime, nullable=False)  # Usually earnings date + 1 day
    
    # Prediction values
    predicted_return = Column(Float, nullable=False)
    confidence_score = Column(Float, nullable=False)  # 0-1 scale
    direction = Column(String(10), nullable=False)  # UP, DOWN, NEUTRAL
    
    # Model information
    model_version = Column(String(50), nullable=False)
    features_used = Column(JSON, nullable=True)
    
    # Actual results (filled after target date)
    actual_return = Column(Float, nullable=True)
    prediction_accuracy = Column(Float, nullable=True)
    
    # AI-generated reasoning
    reasoning = Column(Text, nullable=True)
    similar_scenarios = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())