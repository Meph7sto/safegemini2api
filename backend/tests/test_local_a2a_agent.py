"""Tests for the local A2A agent service."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from backend.services.local_a2a_agent import app


def _streaming_request_body() -> dict:
    return {
        "jsonrpc": "2.0",
        "id": "req-1",
        "method": "message/stream",
        "params": {
            "message": {
                "kind": "message",
                "messageId": "msg-1",
                "role": "user",
                "parts": [{"kind": "text", "text": "hello"}],
            }
        },
    }


class TestLocalA2AAgent:
    def test_agent_card(self):
        with TestClient(app) as client:
            resp = client.get("/agent-card")
        assert resp.status_code == 200
        payload = resp.json()
        assert payload["protocolVersion"] == "0.3.0"
        assert payload["url"] == "http://localhost:10000"

    def test_message_send(self):
        with patch(
            "backend.services.local_a2a_agent._gemini_client.generate",
            new_callable=AsyncMock,
            return_value={"text": "pong", "raw": {}, "stderr": ""},
        ):
            with TestClient(app) as client:
                resp = client.post(
                    "/",
                    json={
                        "jsonrpc": "2.0",
                        "id": "req-1",
                        "method": "message/send",
                        "params": {
                            "message": {
                                "kind": "message",
                                "messageId": "msg-1",
                                "role": "user",
                                "parts": [{"kind": "text", "text": "ping"}],
                            }
                        },
                    },
                )

        assert resp.status_code == 200
        payload = resp.json()
        assert payload["result"]["role"] == "agent"
        assert payload["result"]["parts"][0]["text"] == "pong"

    def test_message_stream(self):
        async def fake_stream_generate(**_: object):
            yield "hello "
            yield "world"

        with patch(
            "backend.services.local_a2a_agent._gemini_client.stream_generate",
            new=fake_stream_generate,
        ):
            with TestClient(app) as client:
                with client.stream("POST", "/", json=_streaming_request_body()) as resp:
                    body = "".join(resp.iter_text())

        assert resp.status_code == 200
        assert "data:" in body
        assert '"role": "agent"' in body
        assert '"text": "hello "' in body
        assert '"text": "world"' in body
