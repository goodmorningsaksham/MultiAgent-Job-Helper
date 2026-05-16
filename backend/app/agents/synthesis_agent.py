import json
import time
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.models.models import Company, AgentRun
from app.services.llm_service import get_llm_service
from app.prompts.synthesis_prompts import SYNTHESIS_SYSTEM_PROMPT, SYNTHESIS_USER_PROMPT

logger = structlog.get_logger(__name__)


class SynthesisAgent:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm = get_llm_service()

    async def synthesize(
        self,
        company: Company,
        research_data: dict,
        tech_data: dict,
        people_data: dict,
    ) -> dict:
        start_time = time.time()
        agent_run = AgentRun(
            company_id=company.id,
            agent_type="synthesis",
            status="in_progress",
            started_at=datetime.utcnow(),
        )
        self.db.add(agent_run)
        await self.db.flush()

        try:
            response = await self.llm.generate(
                system_prompt=SYNTHESIS_SYSTEM_PROMPT,
                user_message=SYNTHESIS_USER_PROMPT.format(
                    company_name=company.name,
                    research_data=json.dumps(research_data, indent=2)[:4000],
                    tech_stack_data=json.dumps(tech_data, indent=2)[:2000],
                    people_data=json.dumps(people_data, indent=2)[:2000],
                ),
                temperature=0.4,
                max_tokens=4000,
            )

            synthesis_data = self._parse_json_response(response.content)

            company.summary = synthesis_data.get("executive_summary", "")
            company.description = synthesis_data.get("executive_summary", "")
            company.tech_stack = tech_data
            company.hiring_trends = research_data.get("hiring_signals", {})

            if "key_facts" in synthesis_data:
                facts = synthesis_data["key_facts"]
                company.industry = facts.get("industry") or company.industry
                company.size = facts.get("size") or company.size
                company.location = facts.get("location") or company.location

            company.meta_data = {
                **(company.meta_data or {}),
                "synthesis": synthesis_data,
                "completed_steps": (company.meta_data or {}).get("completed_steps", []) + ["synthesis"],
            }

            duration_ms = int((time.time() - start_time) * 1000)
            agent_run.status = "completed"
            agent_run.output_data = synthesis_data
            agent_run.tokens_used = response.tokens_used
            agent_run.duration_ms = duration_ms
            agent_run.completed_at = datetime.utcnow()
            await self.db.flush()

            logger.info(
                "synthesis_complete",
                company=company.name,
                duration_ms=duration_ms,
            )

            return synthesis_data

        except Exception as e:
            agent_run.status = "failed"
            agent_run.error_message = str(e)
            agent_run.completed_at = datetime.utcnow()
            await self.db.flush()
            logger.exception("synthesis_agent_failed", company=company.name)
            raise

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
