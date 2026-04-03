"""OpenAI-compatible API routes.

Implements:
  - GET  /v1/models
  - POST /v1/chat/completions  (non-streaming & SSE streaming)

Port of adapter-server.js request handler logic.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse

from backend.config import Settings
from backend.middleware.auth import get_auth_checker
from backend.models.schemas import (
    ChatCompletionRequest,
    DeltaContent,
    make_chunk,
    make_completion,
    make_error,
    new_chat_id,
)
from backend.services.gemini_client import GeminiCliClient, GeminiCliError
from backend.services.a2a_client import A2AClient, A2AClientError
from backend.services.prompt_builder import (
    build_prompt_from_messages,
    latest_user_message,
    normalize_messages,
    slice_delta_messages,
)

logger = logging.getLogger("safegemini2api")


def create_openai_router(
    settings: Settings,
    gemini_client: GeminiCliClient,
) -> APIRouter:
    """Factory that builds the router with injected dependencies."""

    router = APIRouter(prefix="/v1")

    auth_dependency = get_auth_checker(settings.openai_api_key)

    # Concurrency limiter
    semaphore = asyncio.Semaphore(settings.max_concurrency)

    # A2A client for remote agents
    a2a_client = A2AClient()

    # Session state (only used when context_mode == "session")
    session_states: Dict[str, List[Dict[str, str]]] = {}

    # ── GET /v1/models ───────────────────────────────────────────

    @router.get("/models")
    async def list_models():
        return {
            "object": "list",
            "data": [
                {
                    "id": settings.default_model,
                    "object": "model",
                    "owned_by": "google-gemini-cli",
                }
            ],
        }

    # ── POST /v1/chat/completions ────────────────────────────────

    @router.post("/chat/completions", dependencies=[Depends(auth_dependency)])
    async def chat_completions(body: ChatCompletionRequest, request: Request):
        # Concurrency gate
        if semaphore.locked() and semaphore._value == 0:
            return JSONResponse(
                status_code=429,
                content=make_error(
                    message="Server is busy, retry later",
                    error_type="rate_limit_error",
                ),
            )

        async with semaphore:
            return await _handle_chat(body, request)

    async def _handle_chat(
        body: ChatCompletionRequest,
        request: Request,
    ) -> Any:
        model = body.model or settings.default_model
        raw_messages = [m.model_dump() for m in body.messages]
        normalised = normalize_messages(raw_messages)

        prompt_messages = list(normalised)
        resume = False
        session_id = ""
        should_persist = False

        if settings.context_mode == "session":
            resume = True
            session_id = _resolve_session_key(request, body)
            previous = session_states.get(session_id, [])
            delta = slice_delta_messages(previous, normalised)
            prompt_messages = list(delta) if delta else []

            # Strip leading assistant messages
            while prompt_messages and prompt_messages[0].get("role") == "assistant":
                prompt_messages = prompt_messages[1:]

            if not prompt_messages:
                latest = latest_user_message(normalised)
                prompt_messages = [latest] if latest else list(normalised)

            should_persist = True

        prompt = build_prompt_from_messages(prompt_messages)
        chat_id = new_chat_id()

        connection_mode = body.connection_mode or "local_cli"
        agent_url = body.agent_url.strip() if body.agent_url else ""

        if connection_mode == "local_a2a":
            agent_url = "http://localhost:10000/agent-card"
        elif connection_mode == "remote_agent" and not agent_url:
            return JSONResponse(
                status_code=400,
                content=make_error(
                    message="Agent URL is required for remote agent mode",
                    error_type="invalid_request_error",
                ),
            )

        try:
            if connection_mode in ("local_a2a", "remote_agent"):
                if not body.stream:
                    result = await a2a_client.generate(
                        prompt=prompt,
                        agent_url=agent_url,
                        model=model,
                        timeout_ms=settings.request_timeout_ms,
                        resume=resume,
                        session_id=session_id,
                    )
                    if should_persist:
                        session_states[session_id] = normalised
                    return make_completion(
                        chat_id=chat_id,
                        model=model,
                        content=result["text"],
                    )

                async def _remote_stream():
                    try:
                        yield _sse_frame(
                            make_chunk(
                                chat_id=chat_id,
                                model=model,
                                delta=DeltaContent(role="assistant"),
                            )
                        )

                        async for delta_text in a2a_client.stream_generate(
                            prompt=prompt,
                            agent_url=agent_url,
                            model=model,
                            timeout_ms=settings.request_timeout_ms,
                            resume=resume,
                            session_id=session_id,
                        ):
                            if delta_text:
                                yield _sse_frame(
                                    make_chunk(
                                        chat_id=chat_id,
                                        model=model,
                                        delta=DeltaContent(content=delta_text),
                                    )
                                )

                        yield _sse_frame(
                            make_chunk(
                                chat_id=chat_id,
                                model=model,
                                delta=DeltaContent(),
                                finish_reason="stop",
                            )
                        )
                        yield "data: [DONE]\n\n"

                        if should_persist:
                            session_states[session_id] = normalised

                    except A2AClientError as exc:
                        logger.error("Remote agent request failed: %s", exc)
                        error_payload = _map_a2a_error(exc)
                        yield _sse_frame(error_payload["content"])
                        yield "data: [DONE]\n\n"

                return StreamingResponse(
                    _remote_stream(),
                    media_type="text/event-stream",
                    headers={
                        "cache-control": "no-cache, no-transform",
                        "connection": "keep-alive",
                    },
                )

            if not body.stream:
                result = await gemini_client.generate(
                    prompt=prompt,
                    model=model,
                    timeout_ms=settings.request_timeout_ms,
                    resume=resume,
                    session_id=session_id,
                )
                if should_persist:
                    session_states[session_id] = normalised
                return make_completion(
                    chat_id=chat_id,
                    model=model,
                    content=result["text"],
                )

            # Streaming response
            async def _event_stream():
                try:
                    # Initial role chunk
                    yield _sse_frame(
                        make_chunk(
                            chat_id=chat_id,
                            model=model,
                            delta=DeltaContent(role="assistant"),
                        )
                    )

                    async for delta_text in gemini_client.stream_generate(
                        prompt=prompt,
                        model=model,
                        timeout_ms=settings.request_timeout_ms,
                        resume=resume,
                        session_id=session_id,
                    ):
                        if delta_text:
                            yield _sse_frame(
                                make_chunk(
                                    chat_id=chat_id,
                                    model=model,
                                    delta=DeltaContent(content=delta_text),
                                )
                            )

                    # Final stop chunk
                    yield _sse_frame(
                        make_chunk(
                            chat_id=chat_id,
                            model=model,
                            delta=DeltaContent(),
                            finish_reason="stop",
                        )
                    )
                    yield "data: [DONE]\n\n"

                    if should_persist:
                        session_states[session_id] = normalised

                except GeminiCliError as exc:
                    logger.error("Stream request failed: %s", exc)
                    error_payload = _map_error(exc)
                    yield _sse_frame(error_payload["content"])
                    yield "data: [DONE]\n\n"

            return StreamingResponse(
                _event_stream(),
                media_type="text/event-stream",
                headers={
                    "cache-control": "no-cache, no-transform",
                    "connection": "keep-alive",
                },
            )

        except GeminiCliError as exc:
            logger.error("Request failed: %s", exc)
            mapped = _map_error(exc)
            return JSONResponse(
                status_code=mapped["status"],
                content=mapped["content"],
            )
        except Exception as exc:
            logger.error("Unexpected error: %s", exc)
            return JSONResponse(
                status_code=500,
                content=make_error(
                    message=str(exc) or "Internal server error",
                    error_type="server_error",
                ),
            )

    def _resolve_session_key(request: Request, body: ChatCompletionRequest) -> str:
        header_val = request.headers.get(settings.session_key_header, "").strip()
        if header_val:
            return header_val
        if body.user.strip():
            return body.user.strip()
        return "default"

    return router


def _sse_frame(payload: Any) -> str:
    return f"data: {json.dumps(payload)}\n\n"


def _map_error(exc: GeminiCliError) -> Dict[str, Any]:
    msg = str(exc) or "Gemini CLI execution failed"
    if "timed out" in msg.lower():
        return {
            "status": 504,
            "content": make_error(message=msg, error_type="api_timeout_error"),
        }
    return {
        "status": 502,
        "content": make_error(message=msg, error_type="api_error"),
    }


def _map_a2a_error(exc: A2AClientError) -> Dict[str, Any]:
    msg = str(exc) or "A2A agent request failed"
    if "timeout" in msg.lower():
        return {
            "status": 504,
            "content": make_error(message=msg, error_type="api_timeout_error"),
        }
    return {
        "status": 502,
        "content": make_error(message=msg, error_type="api_error"),
    }
