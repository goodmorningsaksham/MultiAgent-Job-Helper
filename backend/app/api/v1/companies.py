from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID

from app.core.database import get_db
from app.models.models import Company
from app.schemas.schemas import (
    CompanyCreate,
    CompanyResponse,
    CompanyListResponse,
    CompanySearchRequest,
    CompanySearchResult,
    ResearchStartRequest,
    ResearchStatusResponse,
)
from app.services.search_service import get_search_service

router = APIRouter(prefix="/companies", tags=["Companies"])


@router.get("", response_model=CompanyListResponse)
async def list_companies(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    query = select(Company).order_by(Company.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    companies = result.scalars().all()

    count_query = select(func.count(Company.id))
    count_result = await db.execute(count_query)
    total = count_result.scalar()

    return CompanyListResponse(
        companies=[CompanyResponse.model_validate(c) for c in companies],
        total=total,
    )


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(company_id: UUID, db: AsyncSession = Depends(get_db)):
    query = select(Company).where(Company.id == company_id)
    result = await db.execute(query)
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return CompanyResponse.model_validate(company)


@router.post("", response_model=CompanyResponse, status_code=201)
async def create_company(request: CompanyCreate, db: AsyncSession = Depends(get_db)):
    company = Company(
        name=request.name,
        domain=request.domain,
        website=request.website,
        industry=request.industry,
    )
    db.add(company)
    await db.commit()
    await db.refresh(company)
    return CompanyResponse.model_validate(company)


@router.post("/search", response_model=list[CompanySearchResult])
async def search_companies(request: CompanySearchRequest):
    search_service = get_search_service()
    results = await search_service.search_company(request.query)
    return [
        CompanySearchResult(
            name=r.title,
            domain=r.url.split("/")[2] if "/" in r.url else None,
            website=r.url,
            description=r.content[:300] if r.content else None,
        )
        for r in results[:5]
    ]


@router.post("/{company_id}/research", status_code=202)
async def start_research(
    company_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    query = select(Company).where(Company.id == company_id)
    result = await db.execute(query)
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    company.research_status = "in_progress"
    await db.commit()

    from app.agents.orchestrator import run_research_pipeline
    background_tasks.add_task(run_research_pipeline, str(company_id))

    return {"status": "started", "company_id": str(company_id)}


@router.get("/{company_id}/research/status", response_model=ResearchStatusResponse)
async def get_research_status(company_id: UUID, db: AsyncSession = Depends(get_db)):
    query = select(Company).where(Company.id == company_id)
    result = await db.execute(query)
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    return ResearchStatusResponse(
        company_id=company.id,
        status=company.research_status,
        progress=company.meta_data.get("research_progress") if company.meta_data else None,
        completed_steps=company.meta_data.get("completed_steps", []) if company.meta_data else [],
        current_step=company.meta_data.get("current_step") if company.meta_data else None,
    )


@router.delete("/{company_id}", status_code=204)
async def delete_company(company_id: UUID, db: AsyncSession = Depends(get_db)):
    query = select(Company).where(Company.id == company_id)
    result = await db.execute(query)
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    await db.delete(company)
    await db.commit()
