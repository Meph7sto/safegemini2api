"""Pydantic schemas for OpenAI-compatible request / response payloads."""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


# ── Request ──────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    """A single chat message."""

    role: str
    content: Any  # str or list of content parts


class ChatCompletionRequest(BaseModel):
    """POST /v1/chat/completions body."""

    messages: List[ChatMessage] = Field(..., min_length=1)
    model: str = ""
    stream: bool = False
    user: str = ""


# ── Response helpers ─────────────────────────────────────────────────

def new_chat_id() -> str:
    """Generate a unique chat completion ID."""
    return f"chatcmpl-{uuid.uuid4().hex}"


def now_unix() -> int:
    """Unix timestamp in seconds."""
    return int(time.time())


class ChoiceMessage(BaseModel):
    role: str = "assistant"
    content: str = ""


class Choice(BaseModel):
    index: int = 0
    message: ChoiceMessage = Field(default_factory=ChoiceMessage)
    finish_reason: Optional[str] = "stop"


class UsageInfo(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatCompletionResponse(BaseModel):
    id: str = Field(default_factory=new_chat_id)
    object: Literal["chat.completion"] = "chat.completion"
    created: int = Field(default_factory=now_unix)
    model: str = ""
    choices: List[Choice] = Field(default_factory=list)
    usage: UsageInfo = Field(default_factory=UsageInfo)


class DeltaContent(BaseModel):
    role: Optional[str] = None
    content: Optional[str] = None


class StreamChoice(BaseModel):
    index: int = 0
    delta: DeltaContent = Field(default_factory=DeltaContent)
    finish_reason: Optional[str] = None


class ChatCompletionChunk(BaseModel):
    id: str = ""
    object: Literal["chat.completion.chunk"] = "chat.completion.chunk"
    created: int = Field(default_factory=now_unix)
    model: str = ""
    choices: List[StreamChoice] = Field(default_factory=list)


class ErrorDetail(BaseModel):
    message: str
    type: str = "invalid_request_error"
    code: str = ""


class ErrorResponse(BaseModel):
    error: ErrorDetail


# ── Factory functions (immutable – always return new instances) ───────

def make_completion(
    *,
    chat_id: str,
    model: str,
    content: str,
    finish_reason: str = "stop",
) -> Dict[str, Any]:
    """Build a non-streaming completion response dict."""
    return ChatCompletionResponse(
        id=chat_id,
        model=model,
        choices=[
            Choice(
                message=ChoiceMessage(content=content),
                finish_reason=finish_reason,
            )
        ],
    ).model_dump()


def make_chunk(
    *,
    chat_id: str,
    model: str,
    delta: DeltaContent,
    finish_reason: Optional[str] = None,
) -> Dict[str, Any]:
    """Build a single SSE chunk dict."""
    return ChatCompletionChunk(
        id=chat_id,
        model=model,
        choices=[
            StreamChoice(delta=delta, finish_reason=finish_reason)
        ],
    ).model_dump()


def make_error(
    *,
    message: str,
    error_type: str = "invalid_request_error",
    code: str = "",
) -> Dict[str, Any]:
    """Build an error response dict."""
    return ErrorResponse(
        error=ErrorDetail(
            message=message,
            type=error_type,
            code=code or error_type,
        )
    ).model_dump()
