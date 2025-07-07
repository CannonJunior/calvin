from fastapi import APIRouter

from app.api.api_v1.endpoints import (
    companies,
    earnings,
    predictions,
    agents,
    analytics,
)

api_router = APIRouter()

api_router.include_router(companies.router, prefix="/companies", tags=["companies"])
api_router.include_router(earnings.router, prefix="/earnings", tags=["earnings"])
api_router.include_router(predictions.router, prefix="/predictions", tags=["predictions"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])