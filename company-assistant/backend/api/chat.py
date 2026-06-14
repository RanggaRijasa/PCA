"""Authenticated conversations, feedback, and streaming local RAG chat."""

from datetime import datetime, timezone
import json
import logging
import re
from typing import Iterator
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from backend.api.mock_data import ANSWER_TEXT, REMOTE_WORK_SOURCES
from backend.api.models import ChatRequest, CreateConversationRequest, FeedbackRequest, MockChatRequest
from backend.auth.models import UserContext
from backend.auth.session import get_current_user
from backend.db.chat import (
    append_chat_message,
    create_chat_session,
    ensure_chat_session_owner,
    get_chat_session,
    list_chat_sessions,
)
from backend.db.connection import get_connection, transaction
from backend.db.feedback import create_feedback
from backend.llm.ollama_client import (
    OllamaError,
    OllamaModelUnavailableError,
    OllamaOfflineError,
)
from backend.rag.service import get_rag_service


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["chat"])


def _not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"error": "Conversation not found", "code": "CONVERSATION_NOT_FOUND"},
    )


@router.get("/conversations")
def conversations(user: UserContext = Depends(get_current_user)) -> dict[str, list[dict]]:
    connection = get_connection()
    try:
        return {"items": list_chat_sessions(connection, user.id)}
    finally:
        connection.close()


@router.get("/conversations/{conversation_id}")
def conversation_detail(
    conversation_id: str, user: UserContext = Depends(get_current_user)
) -> dict[str, object]:
    connection = get_connection()
    try:
        try:
            return get_chat_session(connection, conversation_id, user.id)
        except KeyError as exc:
            raise _not_found() from exc
    finally:
        connection.close()


@router.post("/conversations", status_code=status.HTTP_201_CREATED)
def create_conversation(
    payload: CreateConversationRequest,
    user: UserContext = Depends(get_current_user),
) -> dict[str, str]:
    with transaction() as connection:
        return create_chat_session(connection, user.id, payload.title)


@router.post("/chat/mock")
def mock_chat(
    payload: MockChatRequest,
    user: UserContext = Depends(get_current_user),
) -> dict[str, object]:
    timestamp = datetime.now(timezone.utc).isoformat()
    user_message_id = f"msg_{uuid4().hex[:12]}"
    assistant_message_id = f"msg_{uuid4().hex[:12]}"
    metadata = {
        "modelName": "mock-model",
        "embeddingModel": "mock-embedding",
        "retrievalTopK": 20,
        "rerankTopN": 5,
        "latencyMs": 420,
        "refused": False,
    }
    with transaction() as connection:
        try:
            ensure_chat_session_owner(connection, payload.conversationId, user.id)
        except KeyError as exc:
            raise _not_found() from exc
        append_chat_message(
            connection, user_message_id, payload.conversationId, "user", payload.message
        )
        append_chat_message(
            connection,
            assistant_message_id,
            payload.conversationId,
            "assistant",
            ANSWER_TEXT,
            sources=REMOTE_WORK_SOURCES,
            metadata=metadata,
        )
    return {
        "messageId": assistant_message_id,
        "answer": ANSWER_TEXT,
        "sources": REMOTE_WORK_SOURCES,
        "metadata": metadata,
        "createdAt": timestamp,
    }


def _sse(event: str, payload: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=True)}\n\n"


def _stream_pieces(text: str) -> Iterator[str]:
    for piece in re.findall(r"\S+\s*", text):
        yield piece


@router.post("/chat")
def real_chat(
    payload: ChatRequest,
    user: UserContext = Depends(get_current_user),
) -> StreamingResponse:
    clean_message = payload.message.strip()
    user_message_id = f"msg_{uuid4().hex[:12]}"
    assistant_message_id = f"msg_{uuid4().hex[:12]}"

    with transaction() as connection:
        try:
            ensure_chat_session_owner(connection, payload.conversationId, user.id)
        except KeyError as exc:
            raise _not_found() from exc
        append_chat_message(
            connection,
            user_message_id,
            payload.conversationId,
            "user",
            clean_message,
        )

    def events() -> Iterator[str]:
        yield _sse(
            "start",
            {"messageId": assistant_message_id, "conversationId": payload.conversationId},
        )
        yield _sse("status", {"stage": "retrieving"})
        try:
            result = get_rag_service().query(
                clean_message,
                user,
                department_filter=payload.departmentFilter,
                source_filter=payload.sourceFilter,
                session_id=payload.conversationId,
                stream_model=True,
            )
            metadata = result.metadata()
            yield _sse("status", {"stage": "streaming"})
            for piece in _stream_pieces(result.answer):
                yield _sse("token", {"content": piece})

            final_status = "refused" if result.refused else "complete"
            with transaction() as connection:
                ensure_chat_session_owner(connection, payload.conversationId, user.id)
                append_chat_message(
                    connection,
                    assistant_message_id,
                    payload.conversationId,
                    "assistant",
                    result.answer,
                    status=final_status,
                    sources=result.sources,
                    metadata=metadata,
                    audit_id=result.audit_id,
                )
            yield _sse(
                "final",
                {
                    "messageId": assistant_message_id,
                    "answer": result.answer,
                    "sources": result.sources,
                    "metadata": metadata,
                    "status": final_status,
                },
            )
        except OllamaOfflineError as exc:
            yield _sse("error", {"error": str(exc), "code": "OLLAMA_OFFLINE"})
        except OllamaModelUnavailableError as exc:
            yield _sse(
                "error", {"error": str(exc), "code": "OLLAMA_MODEL_UNAVAILABLE"}
            )
        except OllamaError as exc:
            yield _sse("error", {"error": str(exc), "code": "OLLAMA_ERROR"})
        except Exception:
            logger.exception("Authenticated RAG request failed")
            yield _sse(
                "error",
                {
                    "error": "The local RAG request failed. Check the backend logs.",
                    "code": "RAG_ERROR",
                },
            )

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/feedback")
def submit_feedback(
    payload: FeedbackRequest,
    user: UserContext = Depends(get_current_user),
) -> dict[str, str]:
    try:
        with transaction() as connection:
            feedback_id = create_feedback(
                connection,
                rating=payload.rating,
                message_id=payload.messageId,
                user_id=user.id,
                comment=payload.comment,
                audit_id=payload.auditId,
            )
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": str(exc), "code": "MESSAGE_NOT_FOUND"},
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": str(exc), "code": "AUDIT_MISMATCH"},
        ) from exc
    return {"status": "ok", "feedbackId": feedback_id}
