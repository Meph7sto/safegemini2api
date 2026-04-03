"""Local A2A Agent service.

Implements an A2A-compliant agent that wraps the Gemini CLI.
Runs on port 10000 and communicates via the A2A protocol.
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any, AsyncGenerator, Dict

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse

from backend.config import load_settings
from backend.services.gemini_client import (
    GeminiCliClient,
    GeminiCliConfig,
    GeminiCliError,
)

logger = logging.getLogger("local_a2a_agent")

app = FastAPI(title="Local A2A Agent")

_settings = load_settings()
_gemini_client = GeminiCliClient(
    GeminiCliConfig(
        command=_settings.gemini_cli_command,
        extra_args=_settings.get_extra_args(),
        workdir=_settings.get_workdir(),
        timeout_ms=_settings.request_timeout_ms,
    )
)

AGENT_CARD = {
    "protocolVersion": "0.3.0",
    "name": "local-gemini-cli-agent",
    "version": "1.0.0",
    "description": "Local A2A agent that wraps Gemini CLI",
    "url": "http://localhost:10000",
    "preferredTransport": "JSONRPC",
    "capabilities": {
        "streaming": True,
    },
    "defaultInputModes": ["text/plain"],
    "defaultOutputModes": ["text/plain", "application/json"],
    "skills": [
        {
            "id": "gemini-cli",
            "name": "Gemini CLI",
            "description": "Runs prompts through the locally installed Gemini CLI.",
            "tags": ["gemini", "cli", "text"],
            "examples": ["Summarize the README"],
        }
    ],
    "supportsAuthenticatedExtendedCard": False,
}


@app.get("/agent-card")
async def get_agent_card():
    """Return the A2A Agent Card."""
    return JSONResponse(content=AGENT_CARD)


@app.get("/.well-known/agent-card.json")
async def get_well_known_agent_card():
    """Return the A2A Agent Card from the recommended well-known path."""
    return JSONResponse(content=AGENT_CARD)


@app.post("/")
async def handle_a2a_request(request: Request):
    """Handle incoming A2A JSON-RPC requests."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(
            status_code=400,
            content={
                "jsonrpc": "2.0",
                "error": {"code": -32700, "message": "Invalid JSON"},
            },
        )

    jsonrpc_id = body.get("id", 1)
    method = body.get("method", "")
    params = body.get("params", {})

    if method not in {"message/send", "message/stream", "agent.sendMessage"}:
        return JSONResponse(
            status_code=200,
            content={
                "jsonrpc": "2.0",
                "id": jsonrpc_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"},
            },
        )

    message = params.get("message", {})
    metadata = params.get("metadata", {}) if isinstance(params.get("metadata"), dict) else {}
    content = _extract_message_text(message)
    stream = method == "message/stream" or bool(params.get("stream", False))
    model = str(metadata.get("model") or _settings.default_model)
    resume = bool(metadata.get("resume"))
    session_id = str(metadata.get("session_id") or "")
    context_id = str(message.get("contextId") or uuid.uuid4().hex)

    if not content:
        return JSONResponse(
            status_code=200,
            content={
                "jsonrpc": "2.0",
                "id": jsonrpc_id,
                "error": {"code": -32602, "message": "Empty message content"},
            },
        )

    if stream:
        return StreamingResponse(
            _stream_gemini(
                jsonrpc_id=jsonrpc_id,
                prompt=content,
                model=model,
                resume=resume,
                session_id=session_id,
                context_id=context_id,
            ),
            media_type="text/event-stream",
            headers={
                "cache-control": "no-cache, no-transform",
                "connection": "keep-alive",
                "x-a2a-streaming": "true",
            },
        )

    try:
        result = await _run_gemini(
            prompt=content,
            model=model,
            resume=resume,
            session_id=session_id,
        )
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "id": jsonrpc_id,
                "result": _make_agent_message(
                    text=result,
                    context_id=context_id,
                ),
            }
        )
    except GeminiCliError as exc:
        return JSONResponse(content=_jsonrpc_error(jsonrpc_id, str(exc)))


def _extract_message_text(message: Any) -> str:
    """Extract prompt text from A2A Message or legacy payloads."""
    if not isinstance(message, dict):
        return ""

    parts = message.get("parts")
    if isinstance(parts, list):
        text = "".join(
            part.get("text", "")
            for part in parts
            if isinstance(part, dict) and part.get("kind") == "text"
        )
        if text:
            return text

    content = message.get("content")
    if isinstance(content, str):
        return content

    return message.get("text", "")


def _make_agent_message(text: str, *, context_id: str) -> Dict[str, Any]:
    """Build a minimal agent message payload."""
    return {
        "kind": "message",
        "messageId": uuid.uuid4().hex,
        "role": "agent",
        "contextId": context_id,
        "parts": [{"kind": "text", "text": text}],
    }


def _jsonrpc_error(jsonrpc_id: Any, message: str, code: int = -32000) -> Dict[str, Any]:
    """Build a JSON-RPC error payload."""
    return {
        "jsonrpc": "2.0",
        "id": jsonrpc_id,
        "error": {"code": code, "message": message},
    }


def _jsonrpc_success(jsonrpc_id: Any, result: Dict[str, Any]) -> str:
    """Build one JSON-RPC response line suitable for SSE framing."""
    return json.dumps({"jsonrpc": "2.0", "id": jsonrpc_id, "result": result})


async def _run_gemini(
    *,
    prompt: str,
    model: str,
    resume: bool,
    session_id: str,
) -> str:
    """Run Gemini CLI and return the output."""
    try:
        result = await _gemini_client.generate(
            prompt=prompt,
            model=model,
            timeout_ms=_settings.request_timeout_ms,
            resume=resume,
            session_id=session_id,
        )
        return result["text"]
    except GeminiCliError as exc:
        logger.error("Gemini CLI error: %s", exc)
        raise


async def _stream_gemini(
    *,
    jsonrpc_id: Any,
    prompt: str,
    model: str,
    resume: bool,
    session_id: str,
    context_id: str,
) -> AsyncGenerator[str, None]:
    """Run Gemini CLI in streaming mode and yield deltas."""
    try:
        async for delta in _gemini_client.stream_generate(
            prompt=prompt,
            model=model,
            timeout_ms=_settings.request_timeout_ms,
            resume=resume,
            session_id=session_id,
        ):
            if not delta:
                continue
            payload = _jsonrpc_success(
                jsonrpc_id,
                _make_agent_message(delta, context_id=context_id),
            )
            yield f"data: {payload}\n\n"
    except GeminiCliError as exc:
        logger.error("Streaming Gemini CLI error: %s", exc)
        yield f"data: {json.dumps(_jsonrpc_error(jsonrpc_id, str(exc)))}\n\n"


def create_agent_app() -> FastAPI:
    """Factory to create the FastAPI agent app."""
    return app


if __name__ == "__main__":
    import uvicorn

    logging.basicConfig(level=logging.INFO)
    uvicorn.run(app, host="0.0.0.0", port=10000, log_level="info")
