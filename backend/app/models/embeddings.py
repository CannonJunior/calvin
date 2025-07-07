from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
import uuid

from app.models.base import Base


class EarningsEmbedding(Base):
    __tablename__ = "earnings_embeddings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_symbol = Column(String(10), nullable=False, index=True)
    
    # Source information
    earnings_date = Column(DateTime, nullable=False)
    quarter = Column(String(10), nullable=False)
    year = Column(Integer, nullable=False)
    
    # Text content
    earnings_call_transcript = Column(Text, nullable=True)
    press_release_text = Column(Text, nullable=True)
    analyst_summary = Column(Text, nullable=True)
    
    # Embeddings (1536 dimensions for OpenAI ada-002)
    call_embedding = Column(Vector(1536), nullable=True)
    press_release_embedding = Column(Vector(1536), nullable=True)
    combined_embedding = Column(Vector(1536), nullable=True)
    
    # Metadata
    sentiment_score = Column(JSON, nullable=True)  # {"positive": 0.8, "negative": 0.1, "neutral": 0.1}
    key_topics = Column(JSON, nullable=True)  # ["revenue_growth", "margin_expansion", etc.]
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class NewsEmbedding(Base):
    __tablename__ = "news_embeddings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_symbol = Column(String(10), nullable=False, index=True)
    
    # News details
    headline = Column(String(500), nullable=False)
    content = Column(Text, nullable=True)
    source = Column(String(100), nullable=True)
    published_date = Column(DateTime, nullable=False)
    
    # Embeddings
    headline_embedding = Column(Vector(1536), nullable=True)
    content_embedding = Column(Vector(1536), nullable=True)
    
    # Analysis
    sentiment_score = Column(JSON, nullable=True)
    relevance_score = Column(Integer, nullable=True)  # 1-10 scale
    
    # Context
    days_to_earnings = Column(Integer, nullable=True)
    market_hours = Column(String(20), nullable=True)  # PRE_MARKET, MARKET, AFTER_HOURS
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AnalystReportEmbedding(Base):
    __tablename__ = "analyst_report_embeddings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_symbol = Column(String(10), nullable=False, index=True)
    
    # Report details
    analyst_firm = Column(String(100), nullable=True)
    analyst_name = Column(String(100), nullable=True)
    report_date = Column(DateTime, nullable=False)
    report_type = Column(String(50), nullable=True)  # INITIATION, UPGRADE, DOWNGRADE, etc.
    
    # Content
    report_title = Column(String(500), nullable=True)
    executive_summary = Column(Text, nullable=True)
    full_content = Column(Text, nullable=True)
    
    # Embeddings
    summary_embedding = Column(Vector(1536), nullable=True)
    content_embedding = Column(Vector(1536), nullable=True)
    
    # Analysis
    recommendation = Column(String(20), nullable=True)  # BUY, HOLD, SELL
    target_price = Column(Integer, nullable=True)
    sentiment_score = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())