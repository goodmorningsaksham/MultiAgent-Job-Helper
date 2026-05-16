import asyncio
import json
import structlog
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from sse_starlette.sse import EventSourceResponse

from app.core.database import get_db, AsyncSessionLocal
from app.models.models import Company

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/stream", tags=["Streaming"])

POLL_DB_INTERVAL = 1.5


@router.get("/research/{company_id}")
async def stream_research_progress(company_id: UUID):
    async def event_generator():
        previous_step = None
        previous_status = None

        while True:
            async with AsyncSessionLocal() as db:
                query = select(Company).where(Company.id == company_id)
                result = await db.execute(query)
                company = result.scalar_one_or_none()

                if not company:
                    yield {
                        "event": "error",
                        "data": json.dumps({"error": "Company not found"}),
                    }
                    return

                meta = company.meta_data or {}
                current_step = meta.get("current_step", "pending")
                completed_steps = meta.get("completed_steps", [])
                status = company.research_status

                if current_step != previous_step or status != previous_status:
                    previous_step = current_step
                    previous_status = status

                    yield {
                        "event": "progress",
                        "data": json.dumps({
                            "status": status,
                            "current_step": current_step,
                            "completed_steps": completed_steps,
                            "company_name": company.name,
                        }),
                    }

                if status in ("completed", "failed"):
                    summary_data = {}
                    if status == "completed":
                        summary_data = {
                            "summary": company.summary,
                            "industry": company.industry,
                            "location": company.location,
                            "has_tech_stack": company.tech_stack is not None,
                            "has_hiring_trends": company.hiring_trends is not None,
                        }

                    yield {
                        "event": "complete",
                        "data": json.dumps({
                            "status": status,
                            "completed_steps": completed_steps,
                            "error": meta.get("error"),
                            **summary_data,
                        }),
                    }
                    return

            await asyncio.sleep(POLL_DB_INTERVAL)

    return EventSourceResponse(event_generator())
