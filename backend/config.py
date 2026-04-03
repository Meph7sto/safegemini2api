"""Application configuration loaded from environment variables."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


def _parse_extra_args(raw: str) -> List[str]:
    """Parse GEMINI_CLI_EXTRA_ARGS from various formats.

    Supports:
      - Standard JSON array: ["--flag","value"]
      - Shorthand array:     [--flag,value]
      - Whitespace-separated: --flag value
    """
    trimmed = raw.strip()
    if not trimmed:
        return []

    # Try standard JSON first
    try:
        parsed = json.loads(trimmed)
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
    except (json.JSONDecodeError, ValueError):
        pass

    # Shorthand bracket notation: [--flag,value]
    if trimmed.startswith("[") and trimmed.endswith("]"):
        inner = trimmed[1:-1].strip()
        items: List[str] = []
        current = ""
        quote = ""

        for char in inner:
            if quote:
                if char == quote:
                    quote = ""
                else:
                    current += char
                continue

            if char in ('"', "'"):
                quote = char
                continue

            if char == ",":
                value = current.strip()
                if value:
                    items.append(value)
                current = ""
                continue

            current += char

        last = current.strip()
        if last:
            items.append(last)

        return items

    # Fallback: whitespace split
    return [item for item in re.split(r"\s+", trimmed) if item]


class Settings(BaseSettings):
    """Immutable application settings derived from environment."""

    host: str = Field(default="127.0.0.1")
    port: int = Field(default=8000, gt=0)
    openai_api_key: str = Field(default="")
    default_model: str = Field(default="gemini-2.5-flash")

    gemini_cli_command: str = Field(default="gemini")
    gemini_cli_extra_args: str = Field(default="")
    gemini_workdir: str = Field(default="")

    context_mode: str = Field(default="stateless")
    session_key_header: str = Field(default="x-session-id")
    session_key_field: str = Field(default="user")

    max_concurrency: int = Field(default=4, gt=0)
    request_timeout_ms: int = Field(default=120000, gt=0)
    max_body_bytes: int = Field(default=2_097_152, gt=0)

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    @field_validator("context_mode")
    @classmethod
    def validate_context_mode(cls, value: str) -> str:
        lower = value.lower()
        return "session" if lower == "session" else "stateless"

    @field_validator("session_key_header")
    @classmethod
    def validate_header(cls, value: str) -> str:
        return value.lower()

    def get_extra_args(self) -> List[str]:
        """Return parsed extra args list (computed, not stored mutation)."""
        return _parse_extra_args(self.gemini_cli_extra_args)

    def get_workdir(self) -> str:
        """Return resolved workdir path."""
        if self.gemini_workdir:
            return str(Path(self.gemini_workdir).resolve())
        return os.getcwd()


def load_settings() -> Settings:
    """Create a frozen Settings instance from the environment."""
    return Settings()
