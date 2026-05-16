import json
import time
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.models.models import Company, ResearchData, AgentRun
from app.services.llm_service import get_llm_service
from app.services.search_service import get_search_service
from app.prompts.research_prompts import (
    RESEARCH_SYSTEM_PROMPT,
    RESEARCH_USER_PROMPT,
    TECH_STACK_SYSTEM_PROMPT,
    TECH_STACK_USER_PROMPT,
)

logger = structlog.get_logger(__name__)


class ResearchAgent:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm = get_llm_service()
        self.search = get_search_service()

    async def research_company(self, company: Company) -> dict:
        start_time = time.time()
        agent_run = AgentRun(
            company_id=company.id,
            agent_type="research",
            status="in_progress",
            started_at=datetime.utcnow(),
        )
        self.db.add(agent_run)
        await self.db.flush()

        try:
            general_results = await self.search.search_company(company.name)
            news_results = await self.search.search_company_news(company.name)
            tech_results = await self.search.search_company_tech_stack(company.name)

            for results, source_type in [
                (general_results, "general"),
                (news_results, "news"),
                (tech_results, "tech"),
            ]:
                for r in results:
                    research_item = ResearchData(
                        company_id=company.id,
                        source_type=source_type,
                        source_url=r.url,
                        title=r.title,
                        content=r.content,
                        relevance_score=r.score,
                    )
                    self.db.add(research_item)

            general_text = self._format_results(general_results)
            news_text = self._format_results(news_results)
            tech_text = self._format_results(tech_results)

            research_response = await self.llm.generate(
                system_prompt=RESEARCH_SYSTEM_PROMPT,
                user_message=RESEARCH_USER_PROMPT.format(
                    company_name=company.name,
                    general_results=general_text,
                    news_results=news_text,
                ),
                temperature=0.3,
                max_tokens=3000,
            )

            tech_response = await self.llm.generate(
                system_prompt=TECH_STACK_SYSTEM_PROMPT,
                user_message=TECH_STACK_USER_PROMPT.format(
                    company_name=company.name,
                    tech_results=tech_text,
                ),
                temperature=0.3,
                max_tokens=2000,
            )

            research_data = self._parse_json_response(research_response.content)
            tech_data = self._parse_json_response(tech_response.content)

            duration_ms = int((time.time() - start_time) * 1000)
            agent_run.status = "completed"
            agent_run.output_data = {"research": research_data, "tech_stack": tech_data}
            agent_run.tokens_used = (research_response.tokens_used or 0) + (tech_response.tokens_used or 0)
            agent_run.duration_ms = duration_ms
            agent_run.completed_at = datetime.utcnow()

            await self.db.flush()

            logger.info(
                "research_complete",
                company=company.name,
                duration_ms=duration_ms,
                sources_collected=len(general_results) + len(news_results) + len(tech_results),
            )

            return {"research": research_data, "tech_stack": tech_data}

        except Exception as e:
            agent_run.status = "failed"
            agent_run.error_message = str(e)
            agent_run.completed_at = datetime.utcnow()
            await self.db.flush()
            logger.exception("research_agent_failed", company=company.name)
            raise

    def _format_results(self, results) -> str:
        formatted = []
        for i, r in enumerate(results, 1):
            formatted.append(f"[{i}] Title: {r.title}\nURL: {r.url}\nContent: {r.content[:500]}\n")
        return "\n---\n".join(formatted) if formatted else "No results found."

    def _parse_json_response(self, content: str) -> dict:
        import re
        match = re.search(r'```(?:json)?\s*(.*?)\s*```', content, re.DOTALL)
        if match:
            content = match.group(1)
        else:
            start = content.find('{')
            end = content.rfind('}')
            if start != -1 and end != -1:
                content = content[start:end+1]
        try:
            return json.loads(content.strip())
        except json.JSONDecodeError:
            logger.warning("json_parse_failed", content_preview=content[:200])
            return {"raw_content": content, "parse_error": True}
