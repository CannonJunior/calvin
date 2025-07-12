from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.company import Company
from app.schemas.company import CompanyOut, CompanyCreate, CompanyUpdate

router = APIRouter()


@router.get("/", response_model=List[CompanyOut])
async def get_companies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    sector: Optional[str] = None,
    sp500_only: bool = True,
    db: AsyncSession = Depends(get_db),
):
    """Get list of companies with optional filtering"""
    query = db.query(Company)
    
    if sp500_only:
        query = query.filter(Company.sp500_constituent == True)
    
    if sector:
        query = query.filter(Company.sector == sector)
    
    companies = await query.offset(skip).limit(limit).all()
    return companies


@router.get("/{symbol}", response_model=CompanyOut)
async def get_company(
    symbol: str,
    db: AsyncSession = Depends(get_db),
):
    """Get company by symbol"""
    company = await db.query(Company).filter(Company.symbol == symbol.upper()).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.post("/", response_model=CompanyOut)
async def create_company(
    company_data: CompanyCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create new company"""
    # Check if company already exists
    existing = await db.query(Company).filter(Company.symbol == company_data.symbol.upper()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Company already exists")
    
    company = Company(**company_data.dict())
    company.symbol = company.symbol.upper()
    
    db.add(company)
    await db.commit()
    await db.refresh(company)
    
    return company


@router.put("/{symbol}", response_model=CompanyOut)
async def update_company(
    symbol: str,
    company_data: CompanyUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update company information"""
    company = await db.query(Company).filter(Company.symbol == symbol.upper()).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    update_data = company_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(company, field, value)
    
    await db.commit()
    await db.refresh(company)
    
    return company


@router.get("/sectors/list")
async def get_sectors(db: AsyncSession = Depends(get_db)):
    """Get list of all sectors"""
    result = await db.execute(
        "SELECT DISTINCT sector FROM companies WHERE sector IS NOT NULL ORDER BY sector"
    )
    sectors = [row[0] for row in result.fetchall()]
    return {"sectors": sectors}