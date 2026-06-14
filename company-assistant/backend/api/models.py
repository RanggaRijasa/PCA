"""Pydantic request models for mock endpoints."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class CreateConversationRequest(BaseModel):
    title: str = Field(default="New chat", min_length=1, max_length=120)


class MockChatRequest(BaseModel):
    conversationId: str = Field(min_length=1)
    message: str = Field(min_length=1, max_length=4000)
    departmentFilter: str = "all"
    sourceFilter: str = "all"


class ChatRequest(BaseModel):
    conversationId: str = Field(min_length=1, max_length=120)
    message: str = Field(min_length=1, max_length=4000)
    departmentFilter: str = Field(default="all", max_length=120)
    sourceFilter: str = Field(default="all", max_length=120)


class FeedbackRequest(BaseModel):
    messageId: str = Field(min_length=1)
    rating: Literal["up", "down"]
    comment: Optional[str] = Field(default=None, max_length=500)
    auditId: Optional[str] = Field(default=None, min_length=1, max_length=120)


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=254)
    password: str = Field(min_length=1, max_length=1024)


class RunIngestionRequest(BaseModel):
    jobId: Optional[str] = Field(default=None, min_length=1, max_length=120)
    documentVersionId: Optional[str] = Field(
        default=None, min_length=1, max_length=120
    )
    reindex: bool = False
