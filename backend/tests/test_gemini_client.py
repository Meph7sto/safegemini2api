"""Tests for backend.services.gemini_client module – unit-level helpers."""

from backend.services.gemini_client import (
    _diff_chunk,
    _extract_assistant_text_from_stream_event,
    _extract_text,
    _safe_json_parse,
)


class TestSafeJsonParse:
    def test_valid_json(self):
        assert _safe_json_parse('{"a": 1}') == {"a": 1}

    def test_invalid_json(self):
        assert _safe_json_parse("not json") is None

    def test_empty_string(self):
        assert _safe_json_parse("") is None


class TestExtractText:
    def test_string(self):
        assert _extract_text("hello") == "hello"

    def test_dict_with_text(self):
        assert _extract_text({"text": "world"}) == "world"

    def test_dict_with_content_string(self):
        assert _extract_text({"content": "foo"}) == "foo"

    def test_dict_with_parts(self):
        assert _extract_text({"parts": [{"text": "a"}, {"text": "b"}]}) == "ab"

    def test_list_of_text_nodes(self):
        assert _extract_text([{"text": "x"}, {"text": "y"}]) == "xy"

    def test_none(self):
        assert _extract_text(None) == ""

    def test_nested_content_array(self):
        assert _extract_text({"content": [{"text": "a"}, {"text": "b"}]}) == "ab"


class TestExtractAssistantFromStream:
    def test_message_event(self):
        event = {
            "type": "message",
            "message": {"role": "assistant", "text": "reply"},
        }
        assert _extract_assistant_text_from_stream_event(event) == "reply"

    def test_ignores_user_role(self):
        event = {
            "type": "message",
            "message": {"role": "user", "text": "question"},
        }
        assert _extract_assistant_text_from_stream_event(event) == ""

    def test_ignores_non_message_type(self):
        event = {"type": "tool_call", "message": {"text": "data"}}
        assert _extract_assistant_text_from_stream_event(event) == ""

    def test_no_type_defaults_to_accept(self):
        event = {"message": {"text": "reply"}}
        assert _extract_assistant_text_from_stream_event(event) == "reply"


class TestDiffChunk:
    def test_initial_chunk(self):
        snapshot, delta = _diff_chunk("", "hello")
        assert snapshot == "hello"
        assert delta == "hello"

    def test_incremental(self):
        snapshot, delta = _diff_chunk("hel", "hello")
        assert snapshot == "hello"
        assert delta == "lo"

    def test_no_new_text(self):
        snapshot, delta = _diff_chunk("hello", "")
        assert snapshot == "hello"
        assert delta == ""

    def test_suffix_match(self):
        snapshot, delta = _diff_chunk("hello world", "world")
        assert snapshot == "hello world"
        assert delta == ""

    def test_no_overlap(self):
        snapshot, delta = _diff_chunk("abc", "xyz")
        assert snapshot == "abcxyz"
        assert delta == "xyz"
