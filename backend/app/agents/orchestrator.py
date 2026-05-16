import json
import structlog
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from sqlalchemy import select
from datetime import datetime

from app.core.database import AsyncSessionLocal
from app.models.models import Company
from app.agents.research_agent import ResearchAgent
from app.agents.people_agent import PeopleAgent
from app.agents.synthesis_agent import SynthesisAgent
from app.agents.evaluator_agent import EvaluatorAgent

logger = structlog.get_logger(__name__)


class ResearchState(TypedDict):
    company_id: str
    company_name: str
    research_data: dict
    tech_data: dict
    people_data: dict
    synthesis_data: dict
    evaluation_data: dict
    current_step: str
    completed_steps: list[str]
    error: str | None


def create_research_graph():
    workflow = StateGraph(ResearchState)

    async def research_node(state: ResearchState) -> ResearchState:
        async with AsyncSessionLocal() as db:
            company = await _get_company(db, state["company_id"])
            company.meta_data = {**(company.meta_data or {}), "current_step": "research"}
            await db.commit()

            agent = ResearchAgent(db)
            result = await agent.research_company(company)
            await db.commit()

            return {
                **state,
                "research_data": result.get("research", {}),
                "tech_data": result.get("tech_stack", {}),
                "current_step": "people",
                "completed_steps": state["completed_steps"] + ["research"],
            }

    async def people_node(state: ResearchState) -> ResearchState:
        async with AsyncSessionLocal() as db:
            company = await _get_company(db, state["company_id"])
            company.meta_data = {**(company.meta_data or {}), "current_step": "people"}
            await db.commit()

            agent = PeopleAgent(db)
            result = await agent.discover_people(company)
            await db.commit()

            return {
                **state,
                "people_data": result,
                "current_step": "synthesis",
                "completed_steps": state["completed_steps"] + ["people"],
            }

    async def synthesis_node(state: ResearchState) -> ResearchState:
        async with AsyncSessionLocal() as db:
            company = await _get_company(db, state["company_id"])
            company.meta_data = {**(company.meta_data or {}), "current_step": "synthesis"}
            await db.commit()

            agent = SynthesisAgent(db)
            result = await agent.synthesize(
                company=company,
                research_data=state["research_data"],
                tech_data=state["tech_data"],
                people_data=state["people_data"],
            )
            await db.commit()

            return {
                **state,
                "synthesis_data": result,
                "current_step": "evaluation",
                "completed_steps": state["completed_steps"] + ["synthesis"],
            }

    async def evaluation_node(state: ResearchState) -> ResearchState:
        async with AsyncSessionLocal() as db:
            company = await _get_company(db, state["company_id"])
            company.meta_data = {**(company.meta_data or {}), "current_step": "evaluation"}
            await db.commit()

            # Embed research data for RAG
            from app.services.embedding_service import EmbeddingService
            embedding_svc = EmbeddingService(db)
            await embedding_svc.embed_research_data(company.id)
            await db.commit()

            evaluator = EvaluatorAgent(db)

            sources_text = json.dumps(state["research_data"], indent=2)[:3000]
            synthesis_text = json.dumps(state["synthesis_data"], indent=2)[:3000]

            eval_result = await evaluator.evaluate(
                content=synthesis_text,
                sources=sources_text,
                content_type="company_synthesis",
                agent_type="synthesis",
                content_id=state["company_id"],
            )

            company.research_status = "completed"
            company.research_completed_at = datetime.utcnow()
            
            # Fetch sources for frontend
            from app.models.models import ResearchData
            res_data = await db.execute(select(ResearchData).where(ResearchData.company_id == company.id))
            records = res_data.scalars().all()
            sources = [{"title": r.title, "url": r.source_url} for r in records]

            company.meta_data = {
                **(company.meta_data or {}),
                "current_step": "complete",
                "completed_steps": state["completed_steps"] + ["evaluation"],
                "evaluation": eval_result,
                "sources": sources,
            }
            await db.commit()

            return {
                **state,
                "evaluation_data": eval_result,
                "current_step": "complete",
                "completed_steps": state["completed_steps"] + ["evaluation"],
            }

    workflow.add_node("research", research_node)
    workflow.add_node("people", people_node)
    workflow.add_node("synthesis", synthesis_node)
    workflow.add_node("evaluation", evaluation_node)

    workflow.set_entry_point("research")
    workflow.add_edge("research", "people")
    workflow.add_edge("people", "synthesis")
    workflow.add_edge("synthesis", "evaluation")
    workflow.add_edge("evaluation", END)

    return workflow.compile()


async def _get_company(db, company_id: str):
    from uuid import UUID
    query = select(Company).where(Company.id == UUID(company_id))
    result = await db.execute(query)
    return result.scalar_one()


async def run_research_pipeline(company_id: str):
    try:
        async with AsyncSessionLocal() as db:
            company = await _get_company(db, company_id)
            company_name = company.name

        graph = create_research_graph()
        initial_state: ResearchState = {
            "company_id": company_id,
            "company_name": company_name,
            "research_data": {},
            "tech_data": {},
            "people_data": {},
            "synthesis_data": {},
            "evaluation_data": {},
            "current_step": "research",
            "completed_steps": [],
            "error": None,
        }

        result = await graph.ainvoke(initial_state)

        logger.info(
            "research_pipeline_complete",
            company_id=company_id,
            company_name=company_name,
            steps_completed=result["completed_steps"],
        )

    except Exception as e:
        logger.exception("research_pipeline_failed", company_id=company_id)
        async with AsyncSessionLocal() as db:
            company = await _get_company(db, company_id)
            company.research_status = "failed"
            company.meta_data = {
                **(company.meta_data or {}),
                "error": str(e),
                "current_step": "failed",
            }
            await db.commit()
