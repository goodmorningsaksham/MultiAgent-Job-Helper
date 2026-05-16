import json
import time
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import datetime

from app.models.models import Company, Person, Template, AgentRun
from app.services.llm_service import get_llm_service
from app.prompts.writer_prompts import (
    WRITER_SYSTEM_PROMPT,
    EMAIL_TEMPLATE_PROMPT,
    INTERVIEW_ANSWER_PROMPT,
)

logger = structlog.get_logger(__name__)


class WriterAgent:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm = get_llm_service()

    async def generate_template(
        self,
        company: Company,
        template_type: str,
        target_person_id: UUID | None = None,
        tone: str = "professional",
        custom_instructions: str | None = None,
    ) -> Template:
        start_time = time.time()
        agent_run = AgentRun(
            company_id=company.id,
            agent_type="writer",
            status="in_progress",
            started_at=datetime.utcnow(),
            input_data={"template_type": template_type, "tone": tone},
        )
        self.db.add(agent_run)
        await self.db.flush()

        try:
            person_info = "No specific target person."
            if target_person_id:
                person_query = select(Person).where(Person.id == target_person_id)
                person_result = await self.db.execute(person_query)
                person = person_result.scalar_one_or_none()
                if person:
                    person_info = (
                        f"Name: {person.name}\n"
                        f"Title: {person.title}\n"
                        f"Recent Activity: {person.activity_summary or 'N/A'}\n"
                        f"Outreach Angle: {(person.meta_data or {}).get('outreach_angle', 'N/A')}"
                    )

            company_summary = company.summary or company.description or f"Company: {company.name}"
            if company.meta_data and "synthesis" in company.meta_data:
                synthesis = company.meta_data["synthesis"]
                company_summary = json.dumps(synthesis, indent=2)[:3000]

            if template_type == "interview_answer":
                prompt = INTERVIEW_ANSWER_PROMPT.format(
                    company_summary=company_summary,
                    question=custom_instructions or "Why do you want to join us?",
                    custom_instructions=custom_instructions or "",
                )
            else:
                prompt = EMAIL_TEMPLATE_PROMPT.format(
                    company_summary=company_summary,
                    person_info=person_info,
                    template_type=template_type,
                    tone=tone,
                    custom_instructions=custom_instructions or "None",
                )

            response = await self.llm.generate(
                system_prompt=WRITER_SYSTEM_PROMPT,
                user_message=prompt,
                temperature=0.7,
                max_tokens=2000,
            )

            content_data = self._parse_json_response(response.content)

            if template_type == "interview_answer":
                title = f"Interview Answer: {(custom_instructions or 'Why join?')[:50]}"
                content = content_data.get("answer", response.content)
            else:
                title = content_data.get("subject", f"{template_type} for {company.name}")
                content = content_data.get("body", response.content)

            template = Template(
                company_id=company.id,
                template_type=template_type,
                title=title,
                content=content,
                target_person_id=target_person_id,
                tone=tone,
                context_used=content_data.get("key_personalization_points"),
                meta_data={"full_response": content_data},
            )
            self.db.add(template)

            duration_ms = int((time.time() - start_time) * 1000)
            agent_run.status = "completed"
            agent_run.output_data = content_data
            agent_run.tokens_used = response.tokens_used
            agent_run.duration_ms = duration_ms
            agent_run.completed_at = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(template)

            logger.info(
                "template_generated",
                company=company.name,
                template_type=template_type,
                duration_ms=duration_ms,
            )

            return template

        except Exception as e:
            agent_run.status = "failed"
            agent_run.error_message = str(e)
            agent_run.completed_at = datetime.utcnow()
            await self.db.flush()
            logger.exception("writer_agent_failed", company=company.name)
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
            return {"body": content}
