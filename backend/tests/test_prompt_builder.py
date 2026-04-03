"""Tests for backend.services.prompt_builder module."""

from backend.services.prompt_builder import (
    build_prompt_from_messages,
    latest_user_message,
    normalize_messages,
    slice_delta_messages,
)


class TestNormalizeMessages:
    """Port of prompt.test.js – normalizeMessages tests."""

    def test_normalises_roles(self):
        msgs = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
            {"role": "function", "content": "result"},  # non-standard → user
        ]
        result = normalize_messages(msgs)
        assert len(result) == 4
        assert result[0]["role"] == "system"
        assert result[3]["role"] == "user"

    def test_skips_empty_content(self):
        msgs = [
            {"role": "user", "content": ""},
            {"role": "user", "content": "   "},
            {"role": "user", "content": "Hello"},
        ]
        result = normalize_messages(msgs)
        assert len(result) == 1
        assert result[0]["content"] == "Hello"

    def test_flattens_content_parts(self):
        msgs = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Hello"},
                    {"type": "text", "text": "World"},
                ],
            }
        ]
        result = normalize_messages(msgs)
        assert result[0]["content"] == "Hello\nWorld"

    def test_returns_new_list(self):
        original = [{"role": "user", "content": "test"}]
        result = normalize_messages(original)
        assert result is not original
        assert result[0] is not original[0]


class TestSliceDeltaMessages:
    def test_returns_delta(self):
        prev = [
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "hello"},
        ]
        curr = [
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "hello"},
            {"role": "user", "content": "how are you?"},
        ]
        result = slice_delta_messages(prev, curr)
        assert len(result) == 1
        assert result[0]["content"] == "how are you?"

    def test_returns_all_on_mismatch(self):
        prev = [{"role": "user", "content": "a"}]
        curr = [{"role": "user", "content": "b"}]
        result = slice_delta_messages(prev, curr)
        assert len(result) == 1
        assert result[0]["content"] == "b"

    def test_empty_previous(self):
        curr = [{"role": "user", "content": "first"}]
        result = slice_delta_messages([], curr)
        assert result == curr
        assert result is not curr  # immutable check


class TestLatestUserMessage:
    def test_finds_last_user(self):
        msgs = [
            {"role": "user", "content": "first"},
            {"role": "assistant", "content": "reply"},
            {"role": "user", "content": "second"},
        ]
        result = latest_user_message(msgs)
        assert result is not None
        assert result["content"] == "second"

    def test_falls_back_to_last(self):
        msgs = [{"role": "assistant", "content": "only"}]
        result = latest_user_message(msgs)
        assert result is not None
        assert result["content"] == "only"

    def test_returns_none_for_empty(self):
        result = latest_user_message([])
        assert result is None


class TestBuildPrompt:
    def test_creates_prompt_with_preamble(self):
        msgs = [{"role": "user", "content": "Hello!"}]
        result = build_prompt_from_messages(msgs)
        assert "chat-completions API" in result
        assert "[user]" in result
        assert "Hello!" in result
        assert isinstance(result, str)
