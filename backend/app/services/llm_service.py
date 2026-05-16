from abc import ABC, abstractmethod
from typing import Any
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import structlog

from app.core.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


class LLMResponse(BaseModel):
    content: str
    tokens_used: int | None = None
    model: str = ""
    raw_response: Any = None


class LLMService:
    def __init__(self):
        self._chat_model = ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.gemini_api_key,
            temperature=0.7,
            max_output_tokens=settings.max_tokens_per_call,
        )
        self._embeddings = GoogleGenerativeAIEmbeddings(
            model=settings.gemini_embedding_model,
            google_api_key=settings.gemini_api_key,
        )

    @property
    def chat_model(self) -> ChatGoogleGenerativeAI:
        return self._chat_model

    @property
    def embeddings(self) -> GoogleGenerativeAIEmbeddings:
        return self._embeddings

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((TimeoutError, ConnectionError)),
    )
    async def generate(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        bind_kwargs = {}
        if temperature != 0.7:
            bind_kwargs["temperature"] = temperature
        if max_tokens:
            bind_kwargs["max_output_tokens"] = max_tokens

        model = self._chat_model.bind(**bind_kwargs) if bind_kwargs else self._chat_model

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message),
        ]

        response = await model.ainvoke(messages)

        token_usage = response.response_metadata.get("usage_metadata", {})
        total_tokens = token_usage.get("total_token_count", 0)

        logger.info(
            "llm_generation_complete",
            model=settings.gemini_model,
            tokens=total_tokens,
        )

        return LLMResponse(
            content=response.content,
            tokens_used=total_tokens,
            model=settings.gemini_model,
        )

    async def generate_structured(
        self,
        system_prompt: str,
        user_message: str,
        output_schema: type[BaseModel],
        temperature: float = 0.4,
    ) -> dict:
        structured_model = self._chat_model.with_structured_output(output_schema)

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message),
        ]

        result = await structured_model.ainvoke(messages)
        return result.model_dump() if isinstance(result, BaseModel) else result

    async def embed_text(self, text: str) -> list[float]:
        return await self._embeddings.aembed_query(text)

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return await self._embeddings.aembed_documents(texts)


_llm_service: LLMService | None = None


def get_llm_service() -> LLMService:
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
