from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.core.database import get_db
from app.models.models import Conversation, ChatMessage, Company
from app.schemas.schemas import ChatRequest, ChatResponse, ChatMessageResponse

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
async def send_message(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    company_query = select(Company).where(Company.id == request.company_id)
    company_result = await db.execute(company_query)
    company = company_result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    if request.conversation_id:
        conv_query = select(Conversation).where(Conversation.id == request.conversation_id)
        conv_result = await db.execute(conv_query)
        conversation = conv_result.scalar_one_or_none()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conversation = Conversation(company_id=request.company_id, title=request.message[:100])
        db.add(conversation)
        await db.flush()

    user_msg = ChatMessage(
        conversation_id=conversation.id,
        role="user",
        content=request.message,
    )
    db.add(user_msg)
    await db.flush()

    from app.agents.chat_agent import ChatAgent
    chat_agent = ChatAgent(db)
    response_content, sources, eval_scores = await chat_agent.respond(
        company=company,
        conversation_id=conversation.id,
        user_message=request.message,
    )

    assistant_msg = ChatMessage(
        conversation_id=conversation.id,
        role="assistant",
        content=response_content,
        sources_used=sources,
        evaluation_scores=eval_scores,
    )
    db.add(assistant_msg)
    await db.commit()

    return ChatResponse(
        conversation_id=conversation.id,
        message=ChatMessageResponse.model_validate(assistant_msg),
        related_sources=sources,
    )


@router.get("/conversations/{company_id}")
async def list_conversations(company_id: UUID, db: AsyncSession = Depends(get_db)):
    query = (
        select(Conversation)
        .where(Conversation.company_id == company_id)
        .order_by(Conversation.created_at.desc())
    )
    result = await db.execute(query)
    conversations = result.scalars().all()
    return [
        {
            "id": str(c.id),
            "title": c.title,
            "created_at": c.created_at.isoformat(),
        }
        for c in conversations
    ]


@router.get("/messages/{conversation_id}", response_model=list[ChatMessageResponse])
async def get_messages(conversation_id: UUID, db: AsyncSession = Depends(get_db)):
    query = (
        select(ChatMessage)
        .where(ChatMessage.conversation_id == conversation_id)
        .order_by(ChatMessage.created_at.asc())
    )
    result = await db.execute(query)
    messages = result.scalars().all()
    return [ChatMessageResponse.model_validate(m) for m in messages]
