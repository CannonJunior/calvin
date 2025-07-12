from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
import json

from app.schemas.agents import AgentResponse
from agents.analysis_agent import AnalysisAgent
from agents.research_agent import ResearchAgent
from agents.prediction_agent import PredictionAgent
from agents.query_agent import QueryAgent


class AgentOrchestrator:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.agents = {
            "analysis": AnalysisAgent(),
            "research": ResearchAgent(),
            "prediction": PredictionAgent(),
            "query": QueryAgent(),
        }
        
    async def process_query(
        self,
        query: str,
        agent_type: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> AgentResponse:
        """Process query with appropriate agent"""
        
        start_time = datetime.now()
        
        # Auto-select agent if not specified
        if not agent_type:
            agent_type = self._select_agent(query)
        
        if agent_type not in self.agents:
            agent_type = "query"  # Default fallback
        
        agent = self.agents[agent_type]
        
        # Check agent health
        if not await agent.health_check():
            return AgentResponse(
                agent_type=agent_type,
                response=f"Agent {agent_type} is not available. Please check Ollama service.",
                confidence=0.0,
                timestamp=datetime.now(),
                processing_time=0.0,
            )
        
        try:
            # Prepare input data
            input_data = {
                "query": query,
                "context": context or {},
                "timestamp": datetime.now().isoformat(),
            }
            
            # Process with selected agent
            result = await agent.process(input_data)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return AgentResponse(
                agent_type=agent_type,
                response=result.get("response", result.get("analysis", str(result))),
                confidence=result.get("confidence", 0.8),
                sources=result.get("sources", []),
                metadata=result.get("metadata", {}),
                timestamp=datetime.now(),
                processing_time=processing_time,
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return AgentResponse(
                agent_type=agent_type,
                response=f"Error processing query: {str(e)}",
                confidence=0.0,
                sources=[],
                metadata={"error": str(e)},
                timestamp=datetime.now(),
                processing_time=processing_time,
            )
    
    async def analyze_company(
        self,
        symbol: str,
        analysis_type: str = "earnings_pattern",
    ) -> Dict[str, Any]:
        """Perform company analysis using analysis agent"""
        
        # Get company data from database
        earnings_data = await self._get_earnings_data(symbol)
        market_data = await self._get_market_data(symbol)
        
        input_data = {
            "symbol": symbol,
            "analysis_type": analysis_type,
            "earnings_data": earnings_data,
            "market_data": market_data,
        }
        
        analysis_agent = self.agents["analysis"]
        result = await analysis_agent.process(input_data)
        
        return result
    
    async def research_company(
        self,
        symbol: str,
        focus: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Research company using research agent"""
        
        # Get recent news and reports
        news_data = await self._get_news_data(symbol)
        analyst_reports = await self._get_analyst_reports(symbol)
        
        input_data = {
            "symbol": symbol,
            "research_type": "market_intelligence",
            "focus_areas": [focus] if focus else ["earnings", "guidance", "sentiment"],
            "news_data": news_data,
            "analyst_reports": analyst_reports,
        }
        
        research_agent = self.agents["research"]
        result = await research_agent.process(input_data)
        
        return result
    
    async def find_similar_scenarios(
        self,
        symbol: str,
        scenario_type: str = "earnings",
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Find similar historical scenarios using query agent"""
        
        input_data = {
            "symbol": symbol,
            "query_type": "similar_scenarios",
            "scenario_type": scenario_type,
            "limit": limit,
        }
        
        query_agent = self.agents["query"]
        result = await query_agent.process(input_data)
        
        return result.get("scenarios", [])
    
    async def explain_prediction(self, prediction_id: str) -> Dict[str, Any]:
        """Explain a prediction using prediction agent"""
        
        # Get prediction data
        prediction_data = await self._get_prediction_data(prediction_id)
        
        input_data = {
            "prediction_id": prediction_id,
            "prediction_data": prediction_data,
            "explanation_type": "detailed",
        }
        
        prediction_agent = self.agents["prediction"]
        result = await prediction_agent.process(input_data)
        
        return result
    
    async def process_chat_message(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        user_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Process chat message with context awareness"""
        
        # Determine best agent for the message
        agent_type = self._select_agent(message)
        
        # Add conversation context
        context = user_context or {}
        if conversation_id:
            context["conversation_id"] = conversation_id
        
        response = await self.process_query(
            query=message,
            agent_type=agent_type,
            context=context,
        )
        
        # Generate follow-up suggestions
        suggestions = self._generate_suggestions(message, response.response)
        
        return {
            "response": response.response,
            "agent_type": agent_type,
            "confidence": response.confidence,
            "suggestions": suggestions,
            "conversation_id": conversation_id or f"conv_{datetime.now().timestamp()}",
            "timestamp": datetime.now().isoformat(),
        }
    
    async def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents"""
        status = {}
        
        for agent_name, agent in self.agents.items():
            try:
                is_healthy = await agent.health_check()
                status[agent_name] = {
                    "status": "healthy" if is_healthy else "unhealthy",
                    "model": agent.model_name,
                    "last_checked": datetime.now().isoformat(),
                }
            except Exception as e:
                status[agent_name] = {
                    "status": "error",
                    "error": str(e),
                    "last_checked": datetime.now().isoformat(),
                }
        
        return {
            "agents": status,
            "overall_status": "healthy" if all(
                s.get("status") == "healthy" for s in status.values()
            ) else "degraded",
            "timestamp": datetime.now().isoformat(),
        }
    
    def _select_agent(self, query: str) -> str:
        """Auto-select appropriate agent based on query content"""
        query_lower = query.lower()
        
        # Analysis keywords
        if any(keyword in query_lower for keyword in [
            "analyze", "analysis", "pattern", "correlation", "trend", "historical"
        ]):
            return "analysis"
        
        # Research keywords
        elif any(keyword in query_lower for keyword in [
            "news", "research", "sentiment", "report", "intelligence", "market"
        ]):
            return "research"
        
        # Prediction keywords
        elif any(keyword in query_lower for keyword in [
            "predict", "forecast", "outlook", "future", "target", "price"
        ]):
            return "prediction"
        
        # Default to query agent for general questions
        else:
            return "query"
    
    def _generate_suggestions(self, original_message: str, response: str) -> List[str]:
        """Generate follow-up suggestions based on conversation"""
        suggestions = [
            "Show me the historical earnings performance",
            "What are the key risk factors?",
            "Compare this to sector peers",
            "Analyze the latest analyst reports",
            "Generate a prediction for next quarter",
        ]
        
        # Context-aware suggestions based on original message
        message_lower = original_message.lower()
        
        if "earnings" in message_lower:
            suggestions = [
                "Show earnings surprise history",
                "Analyze post-earnings stock performance",
                "Compare to analyst expectations",
                "Find similar earnings patterns",
            ]
        elif "prediction" in message_lower:
            suggestions = [
                "Explain the prediction methodology",
                "Show confidence intervals",
                "Find similar historical scenarios",
                "Analyze key risk factors",
            ]
        elif "sentiment" in message_lower:
            suggestions = [
                "Analyze recent news sentiment",
                "Compare to historical sentiment",
                "Show analyst rating changes",
                "Track social media sentiment",
            ]
        
        return suggestions[:4]  # Limit to 4 suggestions
    
    async def _get_earnings_data(self, symbol: str) -> List[Dict[str, Any]]:
        """Get earnings data for a company"""
        try:
            from app.models.company import EarningsEvent
            
            earnings = await self.db.query(EarningsEvent).filter(
                EarningsEvent.company_symbol == symbol
            ).order_by(EarningsEvent.earnings_date.desc()).limit(12).all()
            
            return [
                {
                    "earnings_date": e.earnings_date.isoformat() if e.earnings_date else None,
                    "quarter": e.quarter,
                    "year": e.year,
                    "actual_eps": e.actual_eps,
                    "expected_eps": e.expected_eps,
                    "surprise_percentage": e.surprise_percentage,
                    "return_1d": e.return_1d,
                    "relative_return_1d": e.relative_return_1d,
                }
                for e in earnings
            ]
        except Exception:
            return []
    
    async def _get_market_data(self, symbol: str) -> Dict[str, Any]:
        """Get market data for a company"""
        try:
            from app.models.company import Company
            
            company = await self.db.query(Company).filter(
                Company.symbol == symbol
            ).first()
            
            if company:
                return {
                    "sector": company.sector,
                    "market_cap": company.market_cap,
                    "pe_ratio": company.pe_ratio,
                    "eps": company.eps,
                }
            return {}
        except Exception:
            return {}
    
    async def _get_news_data(self, symbol: str) -> List[Dict[str, Any]]:
        """Get recent news data for a company"""
        # In production, this would fetch from news API or database
        return []
    
    async def _get_analyst_reports(self, symbol: str) -> List[Dict[str, Any]]:
        """Get recent analyst reports for a company"""
        try:
            from app.models.company import AnalystRating
            
            ratings = await self.db.query(AnalystRating).filter(
                AnalystRating.company_symbol == symbol
            ).order_by(AnalystRating.rating_date.desc()).limit(10).all()
            
            return [
                {
                    "analyst_firm": r.analyst_firm,
                    "rating": r.rating,
                    "target_price": r.target_price,
                    "rating_date": r.rating_date.isoformat() if r.rating_date else None,
                }
                for r in ratings
            ]
        except Exception:
            return []
    
    async def _get_prediction_data(self, prediction_id: str) -> Dict[str, Any]:
        """Get prediction data by ID"""
        try:
            from app.models.company import Prediction
            
            prediction = await self.db.query(Prediction).filter(
                Prediction.id == prediction_id
            ).first()
            
            if prediction:
                return {
                    "company_symbol": prediction.company_symbol,
                    "predicted_return": prediction.predicted_return,
                    "confidence_score": prediction.confidence_score,
                    "direction": prediction.direction,
                    "features_used": prediction.features_used,
                    "model_version": prediction.model_version,
                    "target_date": prediction.target_date.isoformat() if prediction.target_date else None,
                }
            return {}
        except Exception:
            return {}