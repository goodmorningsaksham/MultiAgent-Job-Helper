import enum


class ResearchStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentType(str, enum.Enum):
    RESEARCH = "research"
    PEOPLE = "people"
    SYNTHESIS = "synthesis"
    WRITER = "writer"
    EVALUATOR = "evaluator"
    ORCHESTRATOR = "orchestrator"


class TemplateType(str, enum.Enum):
    EMAIL_COLD_OUTREACH = "email_cold_outreach"
    EMAIL_FOLLOW_UP = "email_follow_up"
    LINKEDIN_CONNECTION = "linkedin_connection"
    LINKEDIN_MESSAGE = "linkedin_message"
    INTERVIEW_ANSWER = "interview_answer"


class EvaluationMetric(str, enum.Enum):
    HALLUCINATION = "hallucination"
    SOURCE_GROUNDING = "source_grounding"
    CONFIDENCE = "confidence"
    RELEVANCE = "relevance"
    COHERENCE = "coherence"
