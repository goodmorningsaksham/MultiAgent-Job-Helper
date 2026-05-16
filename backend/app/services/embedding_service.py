import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from uuid import UUID

from app.models.models import ResearchData
from app.services.llm_service import get_llm_service

logger = structlog.get_logger(__name__)

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


class EmbeddingService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm = get_llm_service()

    async def embed_research_data(self, company_id: UUID) -> int:
        query = (
            select(ResearchData)
            .where(ResearchData.company_id == company_id)
            .where(ResearchData.content_embedding.is_(None))
        )
        result = await self.db.execute(query)
        items = result.scalars().all()

        if not items:
            return 0

        texts = []
        item_map = []
        for item in items:
            if not item.content:
                continue
            chunks = self._chunk_text(item.content)
            if chunks:
                texts.append(chunks[0])
                item_map.append(item)

        if not texts:
            return 0

        batch_size = 20
        embedded_count = 0

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_items = item_map[i:i + batch_size]

            try:
                embeddings = await self.llm.embed_texts(batch_texts)
                for item, embedding in zip(batch_items, embeddings):
                    item.content_embedding = embedding
                    embedded_count += 1
            except Exception as e:
                logger.error("embedding_batch_failed", batch_start=i, error=str(e))
                continue

        await self.db.flush()
        logger.info("embeddings_generated", company_id=str(company_id), count=embedded_count)
        return embedded_count

    async def similarity_search(
        self,
        company_id: UUID,
        query: str,
        top_k: int = 5,
    ) -> list[ResearchData]:
        query_embedding = await self.llm.embed_text(query)

        # Format embedding as pgvector literal: '[0.1,0.2,...]'
        embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

        sql = text("""
            SELECT id, title, content, source_url, source_type, relevance_score,
                   1 - (content_embedding <=> cast(:embedding as vector)) as similarity
            FROM research_data
            WHERE company_id = cast(:company_id as uuid)
              AND content_embedding IS NOT NULL
            ORDER BY content_embedding <=> cast(:embedding as vector)
            LIMIT :top_k
        """)

        result = await self.db.execute(
            sql,
            {
                "embedding": embedding_str,
                "company_id": str(company_id),
                "top_k": top_k,
            },
        )
        rows = result.fetchall()

        items = []
        for row in rows:
            item_query = select(ResearchData).where(ResearchData.id == row[0])
            item_result = await self.db.execute(item_query)
            item = item_result.scalar_one_or_none()
            if item:
                items.append(item)

        return items

    async def get_relevant_context(
        self,
        company_id: UUID,
        query: str,
        max_chars: int = 3000,
    ) -> str:
        items = await self.similarity_search(company_id, query, top_k=5)

        context_parts = []
        total_chars = 0
        for item in items:
            if not item.content:
                continue
            snippet = item.content[:600]
            if total_chars + len(snippet) > max_chars:
                break
            source_label = f"[{item.source_type}]" if item.source_type else ""
            context_parts.append(f"{source_label} {item.title or 'Source'}:\n{snippet}")
            total_chars += len(snippet)

        return "\n\n---\n\n".join(context_parts) if context_parts else ""

    def _chunk_text(self, text: str) -> list[str]:
        if len(text) <= CHUNK_SIZE:
            return [text]

        chunks = []
        start = 0
        while start < len(text):
            end = start + CHUNK_SIZE
            if end < len(text):
                last_period = text.rfind('.', start, end)
                last_newline = text.rfind('\n', start, end)
                break_point = max(last_period, last_newline)
                if break_point > start + CHUNK_SIZE // 2:
                    end = break_point + 1
            chunks.append(text[start:end].strip())
            start = end - CHUNK_OVERLAP

        return [c for c in chunks if c]
