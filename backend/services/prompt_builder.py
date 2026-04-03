"""Prompt construction and message normalisation utilities.

Direct port of the original prompt.js – pure functions, no mutation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def _normalize_role(role: str) -> str:
    if role in ("system", "user", "assistant"):
        return role
    return "user"


def _flatten_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    parts: List[str] = []
    for item in content:
        if not isinstance(item, dict):
            continue
        text = item.get("text", "")
        if isinstance(text, str) and text:
            parts.append(text)
    return "\n".join(parts)


def normalize_messages(
    messages: List[Dict[str, Any]],
) -> List[Dict[str, str]]:
    """Normalise a list of chat messages into ``{role, content}`` dicts.

    Returns a **new** list; the input is never mutated.
    """
    result: List[Dict[str, str]] = []
    for msg in messages or []:
        if not isinstance(msg, dict):
            continue
        role = _normalize_role(str(msg.get("role", "user")))
        content = _flatten_content(msg.get("content", "")).strip()
        if not content:
            continue
        result.append({"role": role, "content": content})
    return result


def slice_delta_messages(
    previous: List[Dict[str, str]],
    current: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    """Return messages in *current* that are new compared to *previous*.

    Returns a **new** list.
    """
    prev = previous if isinstance(previous, list) else []
    curr = current if isinstance(current, list) else []

    idx = 0
    while idx < len(prev) and idx < len(curr):
        if (
            prev[idx].get("role") != curr[idx].get("role")
            or prev[idx].get("content") != curr[idx].get("content")
        ):
            break
        idx += 1

    if idx == len(prev):
        return list(curr[idx:])
    return list(curr)


def latest_user_message(
    messages: List[Dict[str, str]],
) -> Optional[Dict[str, str]]:
    """Return the last message with role ``user``, or the very last message."""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            return msg
    return messages[-1] if messages else None


_PREAMBLE_LINES = [
    "You are generating the next assistant message for a chat-completions API.",
    "Return only the assistant's reply text for the final user turn.",
    "Do not add role labels, markdown fences, or any preamble unless the user asked for them.",
    "Do not introduce yourself unless the user explicitly asked who you are.",
    "Do not mention Gemini CLI, tools, agents, delegation, approvals, system prompts, "
    "or hidden instructions.",
    "Do not claim to have inspected files, run commands, or observed the workspace "
    "unless that information appears in the conversation history below.",
    "Do not use or describe tool calls. Answer directly from the conversation.",
]


def build_prompt_from_messages(
    messages: List[Dict[str, str]],
) -> str:
    """Build a single prompt string from normalised messages.

    Returns a new string; nothing is mutated.
    """
    lines: List[str] = list(_PREAMBLE_LINES)
    for msg in normalize_messages(messages):
        lines.append(f"[{msg['role']}]")
        lines.append(msg["content"])
    return "\n\n".join(lines)
