"""Integration tests for the OpenAI-compatible API endpoints.

Uses FastAPI TestClient (httpx-based) to verify routes without
actually spawning Gemini CLI.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.config import Settings
from backend.main import create_app


@pytest.fixture()
def settings():
    """Minimal settings for testing."""
    return Settings(
        _env_file=None,
        openai_api_key="test-key-123",
        default_model="test-model",
    )


@pytest.fixture()
def client(settings):
    """FastAPI TestClient with mocked settings."""
    with patch("backend.main.load_settings", return_value=settings):
        app = create_app()
        with TestClient(app) as tc:
            yield tc


class TestHealthz:
    def test_healthz(self, client):
        resp = client.get("/healthz")
        assert resp.status_code == 200
        assert resp.json() == {"ok": True}


class TestListModels:
    def test_returns_model_list(self, client):
        resp = client.get("/v1/models")
        assert resp.status_code == 200
        data = resp.json()
        assert data["object"] == "list"
        assert len(data["data"]) == 1
        assert data["data"][0]["id"] == "test-model"


class TestAuth:
    def test_missing_key_returns_401(self, client):
        resp = client.post(
            "/v1/chat/completions",
            json={"messages": [{"role": "user", "content": "hi"}]},
        )
        assert resp.status_code == 401

    def test_wrong_key_returns_401(self, client):
        resp = client.post(
            "/v1/chat/completions",
            json={"messages": [{"role": "user", "content": "hi"}]},
            headers={"Authorization": "Bearer wrong-key"},
        )
        assert resp.status_code == 401

    def test_correct_key_passes(self, client):
        """Auth should pass; the actual CLI call is mocked to avoid spawning."""
        with patch(
            "backend.services.gemini_client.GeminiCliClient.generate",
            new_callable=AsyncMock,
            return_value={"text": "ok", "raw": "ok", "stderr": ""},
        ):
            resp = client.post(
                "/v1/chat/completions",
                json={"messages": [{"role": "user", "content": "hi"}]},
                headers={"Authorization": "Bearer test-key-123"},
            )
            assert resp.status_code == 200


class TestChatCompletions:
    def test_non_stream(self, client):
        with patch(
            "backend.services.gemini_client.GeminiCliClient.generate",
            new_callable=AsyncMock,
            return_value={"text": "Hello!", "raw": "Hello!", "stderr": ""},
        ):
            resp = client.post(
                "/v1/chat/completions",
                json={
                    "messages": [{"role": "user", "content": "hi"}],
                    "stream": False,
                },
                headers={"Authorization": "Bearer test-key-123"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["object"] == "chat.completion"
            assert data["choices"][0]["message"]["content"] == "Hello!"

    def test_invalid_body_returns_422(self, client):
        resp = client.post(
            "/v1/chat/completions",
            json={"messages": []},
            headers={"Authorization": "Bearer test-key-123"},
        )
        assert resp.status_code == 422

    def test_no_messages_field(self, client):
        resp = client.post(
            "/v1/chat/completions",
            json={},
            headers={"Authorization": "Bearer test-key-123"},
        )
        assert resp.status_code == 422
