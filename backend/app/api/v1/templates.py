from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.core.database import get_db
from app.models.models import Template, Company
from app.schemas.schemas import TemplateGenerateRequest, TemplateResponse

router = APIRouter(prefix="/templates", tags=["Templates"])


@router.get("/{company_id}", response_model=list[TemplateResponse])
async def list_templates(company_id: UUID, db: AsyncSession = Depends(get_db)):
    query = (
        select(Template)
        .where(Template.company_id == company_id)
        .order_by(Template.created_at.desc())
    )
    result = await db.execute(query)
    templates = result.scalars().all()
    return [TemplateResponse.model_validate(t) for t in templates]


@router.post("/generate", response_model=TemplateResponse, status_code=201)
async def generate_template(
    request: TemplateGenerateRequest,
    db: AsyncSession = Depends(get_db),
):
    company_query = select(Company).where(Company.id == request.company_id)
    company_result = await db.execute(company_query)
    company = company_result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    from app.agents.writer_agent import WriterAgent
    writer = WriterAgent(db)
    template = await writer.generate_template(
        company=company,
        template_type=request.template_type,
        target_person_id=request.target_person_id,
        tone=request.tone,
        custom_instructions=request.custom_instructions,
    )

    return TemplateResponse.model_validate(template)


@router.delete("/{template_id}", status_code=204)
async def delete_template(template_id: UUID, db: AsyncSession = Depends(get_db)):
    query = select(Template).where(Template.id == template_id)
    result = await db.execute(query)
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    await db.delete(template)
    await db.commit()
