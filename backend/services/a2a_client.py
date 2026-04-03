"""A2A (Agent-to-Agent) protocol client for remote subagents.

Handles communication with remote agents using the A2A protocol,
which is a JSON-RPC based protocol for agent communication.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Dict, Iterable, List, Optional
from urllib.parse import urlparse, urlunparse

import httpx


class A2AClientError(Exception):
    """Raised when A2A communication fails."""

    def __init__(self, message: str, *, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.details: Dict[str, Any] = details or {}


@dataclass(frozen=True)
class A2AAgentCard:
    """A2A Agent Card containing agent metadata and capabilities."""

    protocol_version: str
    name: str
    version: str
    url: str
    description: Optional[str] = None
    capabilities: Optional[Dict[str, bool]] = None
    default_input_modes: Optional[List[str]] = None
    default_output_modes: Optional[List[str]] = None
    skills: Optional[List[Dict[str, Any]]] = None


@dataclass(frozen=True)
class A2AClientConfig:
    """Configuration for A2A client."""

    timeout_ms: int = 120_000
    headers: Optional[Dict[str, str]] = None


def _parse_agent_card(data: Dict[str, Any]) -> A2AAgentCard:
    """Parse an agent card from a dictionary."""
    return A2AAgentCard(
        protocol_version=data.get("protocolVersion", "0.3.0"),
        name=data.get("name", "unknown"),
        version=data.get("version", "1.0.0"),
        url=data.get("url", ""),
        description=data.get("description"),
        capabilities=data.get("capabilities"),
        default_input_modes=data.get("defaultInputModes"),
        default_output_modes=data.get("defaultOutputModes"),
        skills=data.get("skills"),
    )


def _make_text_message(
    *,
    role: str,
    text: str,
    message_id: Optional[str] = None,
    context_id: str = "",
    task_id: str = "",
) -> Dict[str, Any]:
    """Build a minimal A2A message object containing text parts."""
    payload: Dict[str, Any] = {
        "kind": "message",
        "messageId": message_id or uuid.uuid4().hex,
        "role": role,
        "parts": [{"kind": "text", "text": text}],
    }
    if context_id:
        payload["contextId"] = context_id
    if task_id:
        payload["taskId"] = task_id
    return payload


def _extract_text_parts(parts: Any) -> str:
    """Extract concatenated text from A2A message parts."""
    if isinstance(parts, list):
        return "".join(
            part.get("text", "")
            for part in parts
            if isinstance(part, dict) and part.get("kind") == "text"
        )
    return ""


def _extract_message_text(message: Any) -> str:
    """Extract text from a Message-like object."""
    if not isinstance(message, dict):
        return ""
    parts_text = _extract_text_parts(message.get("parts"))
    if parts_text:
        return parts_text

    legacy_content = message.get("content")
    if isinstance(legacy_content, str):
        return legacy_content

    return message.get("text", "")


def _extract_result_text(result: Any) -> str:
    """Extract text from JSON-RPC A2A results across a few compatible shapes."""
    if isinstance(result, str):
        return result
    if not isinstance(result, dict):
        return ""

    direct = _extract_message_text(result)
    if direct:
        return direct

    for key in ("message", "artifact", "task"):
        nested = result.get(key)
        nested_text = _extract_message_text(nested)
        if nested_text:
            return nested_text
        if isinstance(nested, dict):
            parts_text = _extract_text_parts(nested.get("parts"))
            if parts_text:
                return parts_text

    artifact = result.get("artifact")
    if isinstance(artifact, dict):
        parts_text = _extract_text_parts(artifact.get("parts"))
        if parts_text:
            return parts_text

    return result.get("content") or result.get("delta", "") or ""


def _normalise_agent_card_url(agent_url: str) -> List[str]:
    """Return likely agent card URLs for a user-provided base URL or card URL."""
    parsed = urlparse(agent_url)
    if not parsed.scheme or not parsed.netloc:
        return [agent_url]

    path = parsed.path.rstrip("/")
    if path.endswith("/agent-card") or path.endswith("/agent-card.json"):
        return [agent_url]
    if path.endswith("/.well-known/agent-card.json"):
        return [agent_url]

    base = urlunparse((parsed.scheme, parsed.netloc, "", "", "", "")).rstrip("/")
    if not path:
        return [
            f"{base}/.well-known/agent-card.json",
            f"{base}/agent-card",
        ]

    original = urlunparse(parsed)
    return [
        original,
        f"{original.rstrip('/')}/agent-card",
    ]


class A2AClient:
    """Client for communicating with remote agents via A2A protocol."""

    def __init__(self, config: A2AClientConfig = None) -> None:
        self._config = config or A2AClientConfig()

    async def _fetch_agent_card(self, url: str) -> A2AAgentCard:
        """Fetch the agent card from the remote agent."""
        headers = {"Accept": "application/json"}
        if self._config.headers:
            headers.update(self._config.headers)

        timeout = self._config.timeout_ms / 1000.0
        errors: List[Dict[str, Any]] = []

        try:
            async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
                for candidate in _normalise_agent_card_url(url):
                    try:
                        response = await client.get(candidate)
                        response.raise_for_status()
                        data = response.json()
                        return _parse_agent_card(data)
                    except httpx.HTTPError as exc:
                        errors.append({"url": candidate, "error": str(exc)})
                    except ValueError as exc:
                        errors.append({"url": candidate, "error": str(exc)})
        except httpx.TimeoutException:
            raise A2AClientError(
                f"Timeout fetching agent card after {int(timeout * 1000)}ms",
                details={"url": url},
            )

        raise A2AClientError(
            "Failed to fetch a valid agent card",
            details={"url": url, "attempts": errors},
        )

    def _build_a2a_message(
        self,
        *,
        prompt: str,
        agent_card: A2AAgentCard,
        model: str = "",
        resume: bool = False,
        session_id: str = "",
        stream: bool = False,
    ) -> Dict[str, Any]:
        """Build an A2A JSON-RPC message for sending a task."""
        metadata = {
            "model": model,
            "resume": resume,
            "session_id": session_id,
        }
        return {
            "jsonrpc": "2.0",
            "id": uuid.uuid4().hex,
            "method": "message/stream" if stream else "message/send",
            "params": {
                "message": _make_text_message(role="user", text=prompt),
                "configuration": {
                    "acceptedOutputModes": agent_card.default_output_modes
                    or ["text/plain", "application/json"],
                    "blocking": not stream,
                },
                "metadata": metadata,
            },
        }

    async def generate(
        self,
        prompt: str,
        agent_url: str,
        model: str = "",
        timeout_ms: int = 0,
        resume: bool = False,
        session_id: str = "",
    ) -> Dict[str, Any]:
        """Send a prompt to a remote agent and return the response.

        Returns a dict with 'text' containing the response content.
        """
        timeout = (timeout_ms or self._config.timeout_ms) / 1000.0

        agent_card = await self._fetch_agent_card(agent_url)

        task_payload = self._build_a2a_message(
            prompt=prompt,
            agent_card=agent_card,
            model=model,
            resume=resume,
            session_id=session_id,
        )

        try:
            async with asyncio.timeout(timeout):
                result = await self._send_jsonrpc_request(agent_card.url, task_payload)
                return {"text": result, "raw": result}
        except asyncio.TimeoutError:
            raise A2AClientError(
                f"Timeout after {int(timeout * 1000)}ms",
                details={"agent_url": agent_url},
            )
        except (httpx.HTTPError, ValueError) as exc:
            raise A2AClientError(
                f"A2A request failed: {exc}",
                details={"agent_url": agent_url},
            )

    async def stream_generate(
        self,
        prompt: str,
        agent_url: str,
        model: str = "",
        timeout_ms: int = 0,
        resume: bool = False,
        session_id: str = "",
    ) -> AsyncGenerator[str, None]:
        """Send a prompt to a remote agent and yield streaming response deltas.

        Yields text delta fragments as they arrive.
        """
        timeout = (timeout_ms or self._config.timeout_ms) / 1000.0

        agent_card = await self._fetch_agent_card(agent_url)

        task_payload = self._build_a2a_message(
            prompt=prompt,
            agent_card=agent_card,
            model=model,
            resume=resume,
            session_id=session_id,
            stream=True,
        )

        try:
            async with asyncio.timeout(timeout):
                async for delta in self._stream_jsonrpc_request(
                    agent_card.url, task_payload
                ):
                    yield delta
        except asyncio.TimeoutError:
            raise A2AClientError(
                f"Timeout after {int(timeout * 1000)}ms",
                details={"agent_url": agent_url},
            )
        except (httpx.HTTPError, ValueError) as exc:
            raise A2AClientError(
                f"A2A streaming request failed: {exc}",
                details={"agent_url": agent_url},
            )

    async def _send_jsonrpc_request(self, url: str, payload: Dict[str, Any]) -> str:
        """Send a JSON-RPC request and return the result text."""
        headers = {"Content-Type": "application/json"}
        if self._config.headers:
            headers.update(self._config.headers)

        timeout = self._config.timeout_ms / 1000.0
        async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            body = response.json()

        if "error" in body:
            raise A2AClientError(
                f"JSON-RPC error: {body['error']}",
                details={"url": url, "error": body["error"]},
            )

        text = _extract_result_text(body.get("result"))
        if not text:
            raise A2AClientError(
                "A2A agent returned empty content",
                details={"url": url, "response": body},
            )
        return text

    async def _stream_jsonrpc_request(
        self,
        url: str,
        payload: Dict[str, Any],
    ) -> AsyncGenerator[str, None]:
        """Send a streaming JSON-RPC request and yield deltas."""
        headers = {
            "Accept": "text/event-stream, application/json",
            "Content-Type": "application/json",
        }
        if self._config.headers:
            headers.update(self._config.headers)

        timeout = self._config.timeout_ms / 1000.0
        async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
            async with client.stream("POST", url, json=payload) as response:
                response.raise_for_status()
                async for body in self._iter_stream_payloads(response):
                    if "error" in body:
                        raise A2AClientError(
                            f"JSON-RPC error: {body['error']}",
                            details={"error": body["error"]},
                        )

                    text = _extract_result_text(body.get("result"))
                    if text:
                        yield text

    async def _iter_stream_payloads(
        self,
        response: httpx.Response,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Yield parsed JSON objects from SSE or JSONL streaming responses."""
        data_lines: List[str] = []

        async for line in response.aiter_lines():
            if line.startswith("data:"):
                data_lines.append(line[5:].strip())
                continue

            if not line.strip():
                if data_lines:
                    payload = self._parse_stream_payload(data_lines)
                    data_lines = []
                    if payload is not None:
                        yield payload
                continue

            payload = self._parse_stream_payload([line])
            if payload is not None:
                yield payload

        if data_lines:
            payload = self._parse_stream_payload(data_lines)
            if payload is not None:
                yield payload

    def _parse_stream_payload(
        self,
        lines: Iterable[str],
    ) -> Optional[Dict[str, Any]]:
        """Parse one streamed event payload."""
        raw = "\n".join(line for line in lines if line).strip()
        if not raw or raw == "[DONE]":
            return None
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            return None
