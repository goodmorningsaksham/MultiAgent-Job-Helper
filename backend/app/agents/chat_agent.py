import json
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.models.models import Company, ResearchData, Conversation, ChatMessage
from app.services.llm_service import get_llm_service

logger = structlog.get_logger(__name__)

CHAT_SYSTEM_PROMPT = """You are an AI recruiting assistant helping a job seeker prepare for applications and interviews.

You have access to detailed company research data. Use it to provide specific, grounded answers.

## CRITICAL RULES
1. ONLY use information from the provided company research — never fabricate
2. If you don't have information to answer, say so clearly
3. When answering interview questions, base responses on actual company data
4. Provide actionable, specific advice
5. Cite which research points you're using when relevant

## YOUR CAPABILITIES
- Answer "Why do you want to join us?" using real company data
- Help prepare for behavioral/technical interviews
- Suggest talking points based on company news/culture
- Recommend networking approaches based on people data
- Draft custom outreach messages"""

CHAT_USER_PROMPT = """## COMPANY RESEARCH
{company_context}

## CONVERSATION HISTORY
{conversation_history}

## USER MESSAGE
{user_message}

Respond helpfully using the company research. Be specific and grounded in facts."""


class ChatAgent:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm = get_llm_service()

    async def respond(
        self,
        company: Company,
        conversation_id: UUID,
        user_message: str,
    ) -> tuple[str, list[dict] | None, dict | None]:
        from app.services.embedding_service import EmbeddingService
        embedding_svc = EmbeddingService(self.db)

        rag_context = await embedding_svc.get_relevant_context(
            company_id=company.id,
            query=user_message,
            max_chars=2000,
        )

        company_context = await self._build_company_context(company)
        conversation_history = await self._get_conversation_history(conversation_id)

        full_context = company_context[:3000]
        if rag_context:
            full_context += f"\n\n## RELEVANT RESEARCH (Vector Search Results)\n{rag_context}"

        response = await self.llm.generate(
            system_prompt=CHAT_SYSTEM_PROMPT,
            user_message=CHAT_USER_PROMPT.format(
                company_context=full_context[:5000],
                conversation_history=conversation_history[:2000],
                user_message=user_message,
            ),
            temperature=0.6,
            max_tokens=2000,
        )

        sources = await self._get_relevant_sources(company.id, user_message)

        from app.agents.evaluator_agent import EvaluatorAgent
        evaluator = EvaluatorAgent(self.db)
        eval_scores = await evaluator.evaluate(
            content=response.content,
            sources=full_context[:2000],
            content_type="chat_response",
            agent_type="chat",
            content_id=str(company.id),
        )

        return response.content, sources, eval_scores

    async def _build_company_context(self, company: Company) -> str:
        context_parts = []

        if company.summary:
            context_parts.append(f"## Company Summary\n{company.summary}")

        if company.meta_data and "synthesis" in company.meta_data:
            synthesis = company.meta_data["synthesis"]
            context_parts.append(f"## Detailed Analysis\n{json.dumps(synthesis, indent=2)[:3000]}")

        if company.tech_stack:
            context_parts.append(f"## Tech Stack\n{json.dumps(company.tech_stack, indent=2)[:1000]}")

        if company.hiring_trends:
            context_parts.append(f"## Hiring Trends\n{json.dumps(company.hiring_trends, indent=2)[:1000]}")

        research_query = (
            select(ResearchData)
            .where(ResearchData.company_id == company.id)
            .order_by(ResearchData.relevance_score.desc())
            .limit(10)
        )
        result = await self.db.execute(research_query)
        research_items = result.scalars().all()

        if research_items:
            research_text = "\n".join(
                f"- [{r.source_type}] {r.title}: {r.content[:200]}" for r in research_items
            )
            context_parts.append(f"## Raw Research\n{research_text}")

        return "\n\n".join(context_parts)

    async def _get_conversation_history(self, conversation_id: UUID) -> str:
        query = (
            select(ChatMessage)
            .where(ChatMessage.conversation_id == conversation_id)
            .order_by(ChatMessage.created_at.asc())
            .limit(20)
        )
        result = await self.db.execute(query)
        messages = result.scalars().all()

        history_parts = []
        for msg in messages[-10:]:
            role = "User" if msg.role == "user" else "Assistant"
            history_parts.append(f"{role}: {msg.content[:300]}")

        return "\n".join(history_parts)

    async def _get_relevant_sources(self, company_id: UUID, query: str) -> list[dict]:
        research_query = (
            select(ResearchData)
            .where(ResearchData.company_id == company_id)
            .order_by(ResearchData.relevance_score.desc())
            .limit(5)
        )
        result = await self.db.execute(research_query)
        items = result.scalars().all()

        return [
            {
                "title": item.title,
                "url": item.source_url,
                "type": item.source_type,
                "relevance": item.relevance_score,
            }
            for item in items
            if item.source_url
        ]
