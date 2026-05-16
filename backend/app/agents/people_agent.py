import json
import time
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.models.models import Company, Person, AgentRun
from app.services.llm_service import get_llm_service
from app.services.search_service import get_search_service

logger = structlog.get_logger(__name__)

PEOPLE_SYSTEM_PROMPT = """You are a people intelligence analyst. Your task is to identify key people at a company who would be valuable networking targets for a job seeker.

## CRITICAL RULES
1. Only extract people actually mentioned in the search results
2. Do NOT fabricate names, titles, or LinkedIn URLs
3. Focus on people who are: hiring managers, team leads, recent posters, active in the community
4. Assess relevance based on their visibility and approachability

## OUTPUT FORMAT
Return valid JSON:
{
    "people": [
        {
            "name": "Full Name",
            "title": "Their job title",
            "role_category": "engineering_lead|hiring_manager|recruiter|executive|team_member",
            "linkedin_url": "URL if found, null otherwise",
            "recent_activity": "Brief description of their recent public activity",
            "relevance_score": 0.0-1.0,
            "outreach_angle": "Why/how to approach this person"
        }
    ],
    "networking_strategy": "Brief recommendation on who to prioritize and why"
}"""

PEOPLE_USER_PROMPT = """## COMPANY: {company_name}

## SEARCH RESULTS - PEOPLE
{people_results}

Identify key people at this company for networking purposes. Only include people explicitly mentioned in the results."""


class PeopleAgent:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm = get_llm_service()
        self.search = get_search_service()

    async def discover_people(self, company: Company) -> dict:
        start_time = time.time()
        agent_run = AgentRun(
            company_id=company.id,
            agent_type="people",
            status="in_progress",
            started_at=datetime.utcnow(),
        )
        self.db.add(agent_run)
        await self.db.flush()

        try:
            general_people = await self.search.search_company_people(company.name)
            engineering_people = await self.search.search_company_people(
                company.name, "engineering hiring manager"
            )
            recruiter_people = await self.search.search_company_people(
                company.name, "recruiter talent acquisition"
            )

            all_results = general_people + engineering_people + recruiter_people
            seen_urls = set()
            unique_results = []
            for r in all_results:
                if r.url not in seen_urls:
                    seen_urls.add(r.url)
                    unique_results.append(r)

            results_text = self._format_results(unique_results[:15])

            response = await self.llm.generate(
                system_prompt=PEOPLE_SYSTEM_PROMPT,
                user_message=PEOPLE_USER_PROMPT.format(
                    company_name=company.name,
                    people_results=results_text,
                ),
                temperature=0.3,
                max_tokens=2500,
            )

            people_data = self._parse_json_response(response.content)

            if "people" in people_data:
                for p in people_data["people"]:
                    person = Person(
                        company_id=company.id,
                        name=p.get("name", "Unknown"),
                        title=p.get("title"),
                        role_category=p.get("role_category"),
                        linkedin_url=p.get("linkedin_url"),
                        activity_summary=p.get("recent_activity"),
                        relevance_score=p.get("relevance_score", 0.0),
                        meta_data={"outreach_angle": p.get("outreach_angle")},
                    )
                    self.db.add(person)

            duration_ms = int((time.time() - start_time) * 1000)
            agent_run.status = "completed"
            agent_run.output_data = people_data
            agent_run.tokens_used = response.tokens_used
            agent_run.duration_ms = duration_ms
            agent_run.completed_at = datetime.utcnow()
            await self.db.flush()

            logger.info(
                "people_discovery_complete",
                company=company.name,
                people_found=len(people_data.get("people", [])),
                duration_ms=duration_ms,
            )

            return people_data

        except Exception as e:
            agent_run.status = "failed"
            agent_run.error_message = str(e)
            agent_run.completed_at = datetime.utcnow()
            await self.db.flush()
            logger.exception("people_agent_failed", company=company.name)
            raise

    def _format_results(self, results) -> str:
        formatted = []
        for i, r in enumerate(results, 1):
            formatted.append(f"[{i}] Title: {r.title}\nURL: {r.url}\nContent: {r.content[:400]}\n")
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
            return {"people": [], "parse_error": True}
