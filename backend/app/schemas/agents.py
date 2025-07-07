from typing import Optional, Dict, List, Any
from datetime import datetime
from pydantic import BaseModel
from enum import Enum


class AgentType(str, Enum):
    ANALYSIS = "analysis"
    RESEARCH = "research"
    PREDICTION = "prediction"
    QUERY = "query"


class AgentQueryRequest(BaseModel):
    query: str
    agent_type: Optional[AgentType] = None
    context: Optional[Dict[str, Any]] = None
    max_tokens: Optional[int] = 1000
    temperature: Optional[float] = 0.7


class AgentResponse(BaseModel):
    agent_type: str
    response: str
    confidence: Optional[float] = None
    sources: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime
    processing_time: Optional[float] = None


class ChatMessage(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    agent_used: str
    suggestions: Optional[List[str]] = None
    timestamp: datetime


class AnalysisRequest(BaseModel):
    symbol: str
    analysis_type: str = "earnings_pattern"
    include_charts: bool = False
    depth: str = "standard"  # basic, standard, deep


class ResearchRequest(BaseModel):
    symbol: str
    focus: Optional[str] = None
    sources: Optional[List[str]] = None
    time_horizon: str = "1month"  # 1week, 1month, 3months


class SimilarScenariosRequest(BaseModel):
    symbol: str
    scenario_type: str = "earnings"
    limit: int = 5
    similarity_threshold: float = 0.8


class SimilarScenario(BaseModel):
    company_symbol: str
    date: datetime
    similarity_score: float
    scenario_description: str
    outcome: Dict[str, Any]
    key_factors: List[str]