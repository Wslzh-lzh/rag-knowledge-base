import json

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.deps import get_db
from app.schemas.conversation import ConversationCreate, ConversationRead, ConversationUpdate, MessageCreate, MessageRead
from app.services.conversation_service import ConversationService
from app.services.llm.base import LLMMessage
from app.services.rag.orchestrator import RAGOrchestrator, RAGState

router = APIRouter()
service = ConversationService()
_rag_orchestrator: RAGOrchestrator | None = None


def _get_rag() -> RAGOrchestrator:
    global _rag_orchestrator
    if _rag_orchestrator is None:
        _rag_orchestrator = RAGOrchestrator()
    return _rag_orchestrator


def _build_conversation_history(messages) -> list[LLMMessage]:
    history: list[LLMMessage] = []
    for msg in messages[-10:]:
        if msg.role in {"user", "assistant", "system"}:
            history.append(LLMMessage(role=msg.role, content=msg.content))
    return history


@router.post("", response_model=ConversationRead)
async def create_conversation(
    payload: ConversationCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
) -> ConversationRead:
    conversation = await service.create_conversation(
        db,
        user_id=user.id,
        kb_id=payload.kb_id,
        title=payload.title or "New conversation",
        mode=payload.mode,
    )
    return ConversationRead.model_validate(conversation)


@router.get("", response_model=list[ConversationRead])
async def list_conversations(
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
) -> list[ConversationRead]:
    conversations = await service.list_conversations(db, user_id=user.id)
    return [ConversationRead.model_validate(c) for c in conversations]


@router.get("/{conversation_id}", response_model=ConversationRead)
async def get_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
) -> ConversationRead:
    conversation = await service.get_conversation(db, conversation_id, user_id=user.id)
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return ConversationRead.model_validate(conversation)


@router.patch("/{conversation_id}", response_model=ConversationRead)
async def update_conversation(
    conversation_id: str,
    payload: ConversationUpdate,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
) -> ConversationRead:
    conversation = await service.update_conversation(
        db,
        conversation_id,
        user_id=user.id,
        title=payload.title,
        summary=payload.summary,
    )
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return ConversationRead.model_validate(conversation)


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
) -> dict[str, str]:
    deleted = await service.delete_conversation(db, conversation_id, user_id=user.id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return {"conversation_id": conversation_id, "status": "deleted"}


@router.get("/{conversation_id}/messages", response_model=list[MessageRead])
async def list_messages(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
) -> list[MessageRead]:
    messages = await service.list_messages(db, conversation_id, user_id=user.id)
    return [MessageRead.model_validate(m) for m in messages]


@router.post("/{conversation_id}/messages", response_model=MessageRead)
async def create_message(
    conversation_id: str,
    payload: MessageCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
) -> MessageRead:
    conversation = await service.get_conversation(db, conversation_id, user_id=user.id)
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    user_message = await service.add_message(
        db,
        conversation_id=conversation_id,
        role="user",
        content=payload.content,
    )

    history_msgs = await service.list_messages(db, conversation_id, user_id=user.id)
    conversation_history = _build_conversation_history(history_msgs)

    kb_ids = [conversation.kb_id] if conversation.kb_id else []
    rag = _get_rag()
    result = await rag.answer(
        RAGState(
            query=payload.content,
            knowledge_base_ids=kb_ids,
            conversation_history=conversation_history,
            top_k=5,
        )
    )

    assistant_message = await service.add_message(
        db,
        conversation_id=conversation_id,
        role="assistant",
        content=result.answer,
        citations=[hit.model_dump() for hit in result.citations],
        usage=result.usage,
    )

    _ = user_message
    return MessageRead.model_validate(assistant_message)


@router.post("/{conversation_id}/messages/stream")
async def create_message_stream(
    conversation_id: str,
    payload: MessageCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    conversation = await service.get_conversation(db, conversation_id, user_id=user.id)
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    await service.add_message(
        db,
        conversation_id=conversation_id,
        role="user",
        content=payload.content,
    )

    history_msgs = await service.list_messages(db, conversation_id, user_id=user.id)
    conversation_history = _build_conversation_history(history_msgs)

    kb_ids = [conversation.kb_id] if conversation.kb_id else []
    rag = _get_rag()
    state = RAGState(
        query=payload.content,
        knowledge_base_ids=kb_ids,
        conversation_history=conversation_history,
        top_k=5,
    )

    full_content = ""
    citations = []
    final_usage = {}
    final_debug = {}

    async def event_generator():
        nonlocal full_content, citations, final_usage, final_debug
        async for event in rag.answer_stream(state):
            if event.get("type") == "citations":
                citations = event.get("citations", [])
            elif event.get("type") == "delta":
                full_content += event.get("content", "")
            elif event.get("type") == "done":
                final_usage = event.get("usage", {})
                final_debug = event.get("retrieval_debug", {})
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

        await service.add_message(
            db,
            conversation_id=conversation_id,
            role="assistant",
            content=full_content,
            citations=citations,
            usage=final_usage,
        )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
