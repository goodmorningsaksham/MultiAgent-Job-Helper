import json
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.models.models import Company, Evaluation, AgentRun
from app.services.llm_service import get_llm_service
from app.prompts.evaluator_prompts import EVALUATOR_SYSTEM_PROMPT, EVALUATOR_USER_PROMPT

logger = structlog.get_logger(__name__)


class EvaluatorAgent:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm = get_llm_service()

    async def evaluate(
        self,
        content: str,
        sources: str,
        content_type: str,
        agent_type: str,
        content_id: str,
    ) -> dict:
        try:
            response = await self.llm.generate(
                system_prompt=EVALUATOR_SYSTEM_PROMPT,
                user_message=EVALUATOR_USER_PROMPT.format(
                    content=content[:3000],
                    sources=sources[:3000],
                    content_type=content_type,
                    agent_type=agent_type,
                ),
                temperature=0.2,
                max_tokens=1500,
            )

            eval_data = self._parse_json_response(response.content)

            metrics = [
                ("hallucination", eval_data.get("hallucination_score", 0.5)),
                ("source_grounding", eval_data.get("source_grounding_score", 0.5)),
                ("confidence", eval_data.get("confidence_score", 0.5)),
                ("relevance", eval_data.get("relevance_score", 0.5)),
            ]

            from uuid import UUID
            for metric_name, score in metrics:
                evaluation = Evaluation(
                    agent_type=agent_type,
                    content_id=UUID(content_id) if isinstance(content_id, str) else content_id,
                    content_type=content_type,
                    metric=metric_name,
                    score=score,
                    reasoning=eval_data.get("reasoning"),
                    sources_checked=eval_data.get("flagged_claims"),
                )
                self.db.add(evaluation)

            await self.db.flush()

            logger.info(
                "evaluation_complete",
                content_type=content_type,
                agent_type=agent_type,
                overall_quality=eval_data.get("overall_quality"),
                recommendation=eval_data.get("recommendation"),
            )

            return eval_data

        except Exception as e:
            logger.exception("evaluator_failed", content_type=content_type)
            return {
                "hallucination_score": 0.5,
                "source_grounding_score": 0.5,
                "confidence_score": 0.5,
                "relevance_score": 0.5,
                "overall_quality": 0.5,
                "reasoning": f"Evaluation failed: {str(e)}",
                "recommendation": "review",
            }

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
            return {"overall_quality": 0.5, "reasoning": content}
