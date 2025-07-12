from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
import json

from app.db.database import get_db
from app.services.agent_orchestrator import AgentOrchestrator
from app.schemas.agents import AgentQueryRequest, AgentResponse

router = APIRouter()


@router.post("/query", response_model=AgentResponse)
async def query_agent(
    request: AgentQueryRequest,
    db: AsyncSession = Depends(get_db),
):
    """Send query to AI agents and get response"""
    orchestrator = AgentOrchestrator(db)
    
    try:
        response = await orchestrator.process_query(
            query=request.query,
            agent_type=request.agent_type,
            context=request.context or {},
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent query failed: {str(e)}")


@router.post("/analysis/{symbol}")
async def analyze_company(
    symbol: str,
    analysis_type: str = "earnings_pattern",
    db: AsyncSession = Depends(get_db),
):
    """Perform deep analysis on a company using AI agents"""
    orchestrator = AgentOrchestrator(db)
    
    try:
        result = await orchestrator.analyze_company(
            symbol=symbol.upper(),
            analysis_type=analysis_type,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/research/{symbol}")
async def research_company(
    symbol: str,
    research_focus: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Research company using web scraping and sentiment analysis"""
    orchestrator = AgentOrchestrator(db)
    
    try:
        result = await orchestrator.research_company(
            symbol=symbol.upper(),
            focus=research_focus,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Research failed: {str(e)}")


@router.websocket("/chat")
async def agent_chat_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time agent chat"""
    await websocket.accept()
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Process with agent orchestrator
            # Note: This would need a separate DB session for WebSocket
            orchestrator = AgentOrchestrator(None)  # Would need async session here
            
            response = await orchestrator.process_chat_message(
                message=message.get("message"),
                conversation_id=message.get("conversation_id"),
                user_context=message.get("context", {}),
            )
            
            # Send response back to client
            await websocket.send_text(json.dumps({
                "type": "agent_response",
                "response": response,
                "timestamp": response.get("timestamp"),
            }))
            
    except WebSocketDisconnect:
        print("Client disconnected from agent chat")
    except Exception as e:
        await websocket.send_text(json.dumps({
            "type": "error",
            "error": str(e),
        }))


@router.get("/status")
async def get_agent_status():
    """Get status of all AI agents"""
    orchestrator = AgentOrchestrator(None)
    
    try:
        status = await orchestrator.get_agent_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get agent status: {str(e)}")


@router.post("/similar-scenarios/{symbol}")
async def find_similar_scenarios(
    symbol: str,
    scenario_type: str = "earnings",
    limit: int = 5,
    db: AsyncSession = Depends(get_db),
):
    """Find similar historical scenarios using RAG"""
    orchestrator = AgentOrchestrator(db)
    
    try:
        scenarios = await orchestrator.find_similar_scenarios(
            symbol=symbol.upper(),
            scenario_type=scenario_type,
            limit=limit,
        )
        return scenarios
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to find similar scenarios: {str(e)}")


@router.post("/explain-prediction/{prediction_id}")
async def explain_prediction(
    prediction_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get AI-generated explanation for a prediction"""
    orchestrator = AgentOrchestrator(db)
    
    try:
        explanation = await orchestrator.explain_prediction(prediction_id)
        return explanation
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to explain prediction: {str(e)}")