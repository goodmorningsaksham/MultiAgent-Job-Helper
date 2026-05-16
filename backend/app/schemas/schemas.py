from pydantic import BaseModel, Field
from typing import Any
from uuid import UUID
from datetime import datetime


class CompanySearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=200)


class CompanySearchResult(BaseModel):
    name: str
    domain: str | None = None
    website: str | None = None
    description: str | None = None
    industry: str | None = None


class CompanyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=500)
    domain: str | None = None
    website: str | None = None
    industry: str | None = None


class CompanyResponse(BaseModel):
    id: UUID
    name: str
    domain: str | None = None
    website: str | None = None
    industry: str | None = None
    size: str | None = None
    location: str | None = None
    description: str | None = None
    tech_stack: dict | None = None
    hiring_trends: dict | None = None
    summary: str | None = None
    logo_url: str | None = None
    linkedin_url: str | None = None
    research_status: str
    research_completed_at: datetime | None = None
    meta_data: Any = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CompanyListResponse(BaseModel):
    companies: list[CompanyResponse]
    total: int


class ResearchStartRequest(BaseModel):
    company_id: UUID


class ResearchStatusResponse(BaseModel):
    company_id: UUID
    status: str
    progress: dict | None = None
    completed_steps: list[str] = []
    current_step: str | None = None


class PersonResponse(BaseModel):
    id: UUID
    name: str
    title: str | None = None
    role_category: str | None = None
    linkedin_url: str | None = None
    recent_posts: list | None = None
    activity_summary: str | None = None
    relevance_score: float | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class TemplateGenerateRequest(BaseModel):
    company_id: UUID
    template_type: str
    target_person_id: UUID | None = None
    tone: str = "professional"
    custom_instructions: str | None = Field(None, max_length=1000)


class TemplateResponse(BaseModel):
    id: UUID
    company_id: UUID
    template_type: str
    title: str
    content: str
    tone: str | None = None
    target_person_id: UUID | None = None
    evaluation_scores: dict | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    company_id: UUID
    conversation_id: UUID | None = None
    message: str = Field(..., min_length=1, max_length=5000)


class ChatMessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    sources_used: list | None = None
    evaluation_scores: dict | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class ChatResponse(BaseModel):
    conversation_id: UUID
    message: ChatMessageResponse
    related_sources: list[dict] | None = None


class EvaluationResponse(BaseModel):
    id: UUID
    agent_type: str
    metric: str
    score: float
    reasoning: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class AgentRunResponse(BaseModel):
    id: UUID
    agent_type: str
    status: str
    tokens_used: int | None = None
    duration_ms: int | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None

    class Config:
        from_attributes = True
