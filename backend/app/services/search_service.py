from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any
import structlog

from app.core.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


@dataclass
class SearchResult:
    title: str
    url: str
    content: str
    score: float = 0.0
    raw_content: str | None = None
    meta_data: dict = field(default_factory=dict)


class SearchProvider(ABC):
    @abstractmethod
    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        pass

    @abstractmethod
    async def search_news(self, query: str, max_results: int = 5) -> list[SearchResult]:
        pass


class TavilySearchProvider(SearchProvider):
    def __init__(self):
        from tavily import AsyncTavilyClient
        self._client = AsyncTavilyClient(api_key=settings.tavily_api_key)

    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        try:
            response = await self._client.search(
                query=query,
                max_results=max_results,
                include_raw_content=True,
                search_depth="advanced",
            )
            return [
                SearchResult(
                    title=r.get("title", ""),
                    url=r.get("url", ""),
                    content=r.get("content", ""),
                    score=r.get("score", 0.0),
                    raw_content=r.get("raw_content"),
                )
                for r in response.get("results", [])
            ]
        except Exception as e:
            logger.error("tavily_search_failed", error=str(e), query=query)
            return []

    async def search_news(self, query: str, max_results: int = 5) -> list[SearchResult]:
        try:
            response = await self._client.search(
                query=query,
                max_results=max_results,
                topic="news",
                days=30,
            )
            return [
                SearchResult(
                    title=r.get("title", ""),
                    url=r.get("url", ""),
                    content=r.get("content", ""),
                    score=r.get("score", 0.0),
                )
                for r in response.get("results", [])
            ]
        except Exception as e:
            logger.error("tavily_news_search_failed", error=str(e), query=query)
            return []


class DuckDuckGoSearchProvider(SearchProvider):
    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        from langchain_community.tools import DuckDuckGoSearchResults
        tool = DuckDuckGoSearchResults(num_results=max_results)
        try:
            results = await tool.ainvoke(query)
            if isinstance(results, str):
                return [SearchResult(title="Search Results", url="", content=results)]
            return [
                SearchResult(
                    title=r.get("title", ""),
                    url=r.get("link", ""),
                    content=r.get("snippet", ""),
                )
                for r in results
            ]
        except Exception as e:
            logger.error("ddg_search_failed", error=str(e), query=query)
            return []

    async def search_news(self, query: str, max_results: int = 5) -> list[SearchResult]:
        return await self.search(f"{query} news recent", max_results)


class SearchService:
    def __init__(self, provider: SearchProvider | None = None):
        if provider:
            self._provider = provider
        elif settings.search_provider == "tavily":
            self._provider = TavilySearchProvider()
        elif settings.search_provider == "duckduckgo":
            self._provider = DuckDuckGoSearchProvider()
        else:
            self._provider = TavilySearchProvider()

    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        logger.info("search_executing", query=query, provider=settings.search_provider)
        return await self._provider.search(query, max_results)

    async def search_news(self, query: str, max_results: int = 5) -> list[SearchResult]:
        logger.info("news_search_executing", query=query, provider=settings.search_provider)
        return await self._provider.search_news(query, max_results)

    async def search_company(self, company_name: str) -> list[SearchResult]:
        return await self.search(f"{company_name} company overview about", max_results=5)

    async def search_company_news(self, company_name: str) -> list[SearchResult]:
        return await self.search_news(f"{company_name} latest news hiring", max_results=5)

    async def search_company_tech_stack(self, company_name: str) -> list[SearchResult]:
        return await self.search(f"{company_name} technology stack engineering blog tools", max_results=5)

    async def search_company_people(self, company_name: str, role_filter: str = "") -> list[SearchResult]:
        query = f"{company_name} {role_filter} linkedin people team".strip()
        return await self.search(query, max_results=8)


_search_service: SearchService | None = None


def get_search_service() -> SearchService:
    global _search_service
    if _search_service is None:
        _search_service = SearchService()
    return _search_service
