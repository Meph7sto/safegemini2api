"""Tests for backend.config module."""

import os

import pytest

from backend.config import Settings, _parse_extra_args


class TestParseExtraArgs:
    """Port of config.test.js – parseExtraArgs tests."""

    def test_empty_string(self):
        assert _parse_extra_args("") == []

    def test_standard_json_array(self):
        result = _parse_extra_args('["--flag", "value"]')
        assert result == ["--flag", "value"]

    def test_shorthand_bracket_notation(self):
        result = _parse_extra_args("[--approval-mode,plan]")
        assert result == ["--approval-mode", "plan"]

    def test_shorthand_with_quoted_values(self):
        result = _parse_extra_args('["-NoProfile","-File","C:\\path"]')
        assert result == ["-NoProfile", "-File", "C:\\path"]

    def test_whitespace_separated(self):
        result = _parse_extra_args("--flag value --other")
        assert result == ["--flag", "value", "--other"]

    def test_complex_windows_args(self):
        raw = (
            '["-NoProfile","-ExecutionPolicy","Bypass",'
            '"-File","C:\\\\Users\\\\ASUS\\\\gemini.ps1",'
            '"--approval-mode","yolo"]'
        )
        result = _parse_extra_args(raw)
        assert len(result) == 7
        assert result[0] == "-NoProfile"
        assert result[-1] == "yolo"


class TestSettings:
    """Settings loading with environment variables."""

    def test_defaults(self, monkeypatch):
        # Clear relevant env vars
        for key in (
            "HOST", "PORT", "OPENAI_API_KEY", "DEFAULT_MODEL",
            "GEMINI_CLI_COMMAND", "GEMINI_CLI_EXTRA_ARGS",
            "CONTEXT_MODE", "MAX_CONCURRENCY",
        ):
            monkeypatch.delenv(key, raising=False)

        s = Settings(_env_file=None)
        assert s.host == "127.0.0.1"
        assert s.port == 8000
        assert s.openai_api_key == ""
        assert s.default_model == "gemini-2.5-flash"
        assert s.context_mode == "stateless"

    def test_session_mode(self, monkeypatch):
        monkeypatch.setenv("CONTEXT_MODE", "SESSION")
        s = Settings(_env_file=None)
        assert s.context_mode == "session"

    def test_invalid_context_mode_falls_back(self, monkeypatch):
        monkeypatch.setenv("CONTEXT_MODE", "banana")
        s = Settings(_env_file=None)
        assert s.context_mode == "stateless"
