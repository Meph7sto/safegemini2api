"""Gemini CLI subprocess client.

Async wrapper around the local Gemini CLI binary.  Supports both
single-shot ``generate()`` and streaming ``stream_generate()`` modes.

Direct port of gemini-cli-client.js – all public methods return new
objects; no shared mutable state beyond the read-only config.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional


class GeminiCliError(Exception):
    """Raised when the Gemini CLI process fails."""

    def __init__(self, message: str, *, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.details: Dict[str, Any] = details or {}


# ── Text extraction helpers ──────────────────────────────────────────

def _safe_json_parse(text: str) -> Any:
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return None


def _extract_text(node: Any) -> str:
    if node is None:
        return ""
    if isinstance(node, str):
        return node
    if isinstance(node, list):
        return "".join(filter(None, (_extract_text(item) for item in node)))
    if isinstance(node, dict):
        for key in ("text", "content", "parts", "response"):
            value = node.get(key)
            if isinstance(value, str):
                return value
            if isinstance(value, list):
                return "".join(filter(None, (_extract_text(item) for item in value)))
    return ""


def _should_use_assistant_payload(role: Any) -> bool:
    if not role:
        return True
    return str(role).lower() in ("assistant", "model")


def _extract_assistant_text_from_stream_event(event: Any) -> str:
    if not isinstance(event, dict):
        return ""
    event_type = str(event.get("type") or event.get("event") or "").lower()
    message = event.get("message") or event.get("data") or event.get("delta") or event.get("result") or event
    role = (message.get("role") if isinstance(message, dict) else None) or event.get("role")

    if event_type and event_type not in ("message", "result", "output_text_delta"):
        return ""
    if not _should_use_assistant_payload(role):
        return ""

    return (
        _extract_text(message)
        or _extract_text(event.get("response"))
        or _extract_text(event.get("content"))
        or ""
    )


def _diff_chunk(previous: str, next_text: str) -> tuple[str, str]:
    """Return (snapshot, delta) without mutating inputs."""
    if not next_text:
        return previous, ""
    if not previous:
        return next_text, next_text
    if next_text.startswith(previous):
        return next_text, next_text[len(previous):]
    if previous.endswith(next_text):
        return previous, ""
    return previous + next_text, next_text


# ── Client ───────────────────────────────────────────────────────────

@dataclass(frozen=True)
class GeminiCliConfig:
    """Immutable configuration for the CLI client."""

    command: str = "gemini"
    extra_args: List[str] = field(default_factory=list)
    workdir: str = ""
    timeout_ms: int = 120_000


class GeminiCliClient:
    """Async wrapper around the Gemini CLI binary."""

    def __init__(self, config: GeminiCliConfig) -> None:
        self._config = config

    # ── arg building ──

    def _base_args(self) -> List[str]:
        args = list(self._config.extra_args)
        has_approval = "--approval-mode" in args
        has_yolo = "--yolo" in args or "-y" in args
        if not has_approval and not has_yolo:
            args.extend(["--approval-mode", "plan"])
        return args

    def _build_args(
        self,
        *,
        prompt: str,
        model: str,
        output_format: str,
        resume: bool = False,
        session_id: str = "",
    ) -> List[str]:
        args = self._base_args()
        if resume:
            args.append("--resume")
            if session_id:
                args.append(session_id)
        if model:
            args.extend(["-m", model])
        args.extend(["-p", prompt])
        if output_format:
            args.extend(["--output-format", output_format])
        return args

    # ── single-shot generate ──

    async def generate(
        self,
        *,
        prompt: str,
        model: str = "",
        timeout_ms: int = 0,
        resume: bool = False,
        session_id: str = "",
    ) -> Dict[str, Any]:
        """Run Gemini CLI and return the full response.

        Returns a **new** dict ``{text, raw, stderr}``.
        """
        args = self._build_args(
            prompt=prompt,
            model=model,
            output_format="json",
            resume=resume,
            session_id=session_id,
        )
        timeout = (timeout_ms or self._config.timeout_ms) / 1000.0
        stdout, stderr = await self._run_process(args, timeout)

        trimmed = stdout.strip()
        payload = _safe_json_parse(trimmed)

        if isinstance(payload, dict) and payload.get("error"):
            err_msg = payload["error"].get("message", "Gemini CLI returned an error")
            raise GeminiCliError(err_msg, details={"payload": payload, "stderr": stderr})

        text = ""
        if isinstance(payload, dict):
            text = _extract_text(
                payload.get("response") or payload.get("result") or payload.get("message")
            )
        text = text or trimmed

        if not text:
            raise GeminiCliError("Gemini CLI returned empty output", details={
                "stdout": stdout, "stderr": stderr
            })

        return {"text": text, "raw": payload or trimmed, "stderr": stderr}

    # ── streaming generate ──

    async def stream_generate(
        self,
        *,
        prompt: str,
        model: str = "",
        timeout_ms: int = 0,
        resume: bool = False,
        session_id: str = "",
    ) -> AsyncGenerator[str, None]:
        """Run Gemini CLI in stream-json mode, yielding text deltas.

        Each ``yield`` is a **new** string (delta text fragment).
        """
        args = self._build_args(
            prompt=prompt,
            model=model,
            output_format="stream-json",
            resume=resume,
            session_id=session_id,
        )
        timeout = (timeout_ms or self._config.timeout_ms) / 1000.0

        process = await asyncio.create_subprocess_exec(
            self._config.command,
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self._config.workdir or None,
        )

        snapshot = ""
        try:
            async for delta in self._read_stream(process, timeout):
                candidate = delta
                new_snapshot, diff = _diff_chunk(snapshot, candidate)
                snapshot = new_snapshot
                if diff:
                    yield diff
        finally:
            if process.returncode is None:
                process.kill()
                await process.wait()

    async def _read_stream(
        self,
        process: asyncio.subprocess.Process,
        timeout: float,
    ) -> AsyncGenerator[str, None]:
        """Read stdout line-by-line, parse stream-json events, yield text."""
        assert process.stdout is not None

        async def _read_lines() -> AsyncGenerator[str, None]:
            buffer = ""
            while True:
                chunk = await process.stdout.read(4096)
                if not chunk:
                    break
                buffer += chunk.decode("utf-8", errors="replace")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    stripped = line.strip()
                    if stripped:
                        yield stripped
            if buffer.strip():
                yield buffer.strip()

        try:
            async with asyncio.timeout(timeout):
                async for line in _read_lines():
                    payload = _safe_json_parse(line)
                    if not payload:
                        continue
                    text = _extract_assistant_text_from_stream_event(payload)
                    if text:
                        yield text
        except TimeoutError:
            raise GeminiCliError(
                f"Gemini CLI timed out after {int(timeout * 1000)}ms"
            )

    # ── low-level subprocess runner ──

    async def _run_process(
        self,
        args: List[str],
        timeout: float,
    ) -> tuple[str, str]:
        """Spawn the CLI process and wait for completion."""
        process = await asyncio.create_subprocess_exec(
            self._config.command,
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self._config.workdir or None,
        )
        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            raise GeminiCliError(
                f"Gemini CLI timed out after {int(timeout * 1000)}ms"
            )

        stdout = stdout_bytes.decode("utf-8", errors="replace")
        stderr = stderr_bytes.decode("utf-8", errors="replace")

        if process.returncode != 0:
            raise GeminiCliError(
                f"Gemini CLI exited with code {process.returncode}",
                details={"code": process.returncode, "stdout": stdout, "stderr": stderr},
            )

        return stdout, stderr
