from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from uuid import UUID

from app.core.database import get_db
from app.models.models import Person, Evaluation, AgentRun
from app.schemas.schemas import PersonResponse, EvaluationResponse, AgentRunResponse

router = APIRouter(prefix="/insights", tags=["Insights"])


@router.get("/people/{company_id}", response_model=list[PersonResponse])
async def get_company_people(company_id: UUID, db: AsyncSession = Depends(get_db)):
    query = (
        select(Person)
        .where(Person.company_id == company_id)
        .order_by(Person.relevance_score.desc())
    )
    result = await db.execute(query)
    people = result.scalars().all()
    return [PersonResponse.model_validate(p) for p in people]


@router.get("/evaluations/{company_id}", response_model=list[EvaluationResponse])
async def get_evaluations(
    company_id: UUID,
    agent_type: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    # Evaluations can reference company_id directly as content_id,
    # or reference an AgentRun that belongs to the company
    query = select(Evaluation).where(
        or_(
            Evaluation.content_id == company_id,
            Evaluation.content_id.in_(
                select(AgentRun.id).where(AgentRun.company_id == company_id)
            ),
        )
    )

    if agent_type:
        query = query.where(Evaluation.agent_type == agent_type)

    query = query.order_by(Evaluation.created_at.desc()).limit(50)
    result = await db.execute(query)
    evaluations = result.scalars().all()
    return [EvaluationResponse.model_validate(e) for e in evaluations]


@router.get("/agent-runs/{company_id}", response_model=list[AgentRunResponse])
async def get_agent_runs(company_id: UUID, db: AsyncSession = Depends(get_db)):
    query = (
        select(AgentRun)
        .where(AgentRun.company_id == company_id)
        .order_by(AgentRun.created_at.desc())
        .limit(20)
    )
    result = await db.execute(query)
    runs = result.scalars().all()
    return [AgentRunResponse.model_validate(r) for r in runs]
