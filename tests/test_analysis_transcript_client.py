from __future__ import annotations

import pytest

import src.analysis.transcript_client as transcript_client


class _Snippet:
    def __init__(self, text: str) -> None:
        self.text = text


def test_transcript_client_uses_timeout_session(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class FakeApi:
        def __init__(self, proxy_config=None, http_client=None) -> None:
            captured["timeout"] = getattr(http_client, "_request_timeout_seconds", None)

        def fetch(self, video_id: str, languages=("en",), preserve_formatting: bool = False):
            captured.setdefault("calls", []).append(tuple(languages))  # type: ignore[attr-defined]
            return [_Snippet("hello"), _Snippet("world")]

    monkeypatch.setattr(transcript_client, "YouTubeTranscriptApi", FakeApi)

    client = transcript_client.TranscriptClient(request_timeout_seconds=7.5)
    payload = client.fetch("https://youtu.be/abcdefghijk", language="ko")

    assert captured["timeout"] == 7.5
    assert captured["calls"] == [("ko", "en")]
    assert payload == {
        "video_id": "abcdefghijk",
        "language": "ko",
        "transcript_text": "hello world",
    }


def test_transcript_client_falls_back_to_auto_language(monkeypatch) -> None:
    captured: dict[str, object] = {"calls": 0}

    class FakeApi:
        def __init__(self, proxy_config=None, http_client=None) -> None:
            pass

        def fetch(self, video_id: str, languages=("en",), preserve_formatting: bool = False):
            captured["calls"] = int(captured["calls"]) + 1
            if captured["calls"] == 1:
                raise RuntimeError("preferred language unavailable")
            captured["fallback_languages"] = tuple(languages)
            return [_Snippet("fallback")]

    monkeypatch.setattr(transcript_client, "YouTubeTranscriptApi", FakeApi)

    client = transcript_client.TranscriptClient(request_timeout_seconds=5)
    payload = client.fetch("abcdefghijk", language="ko")

    assert captured["calls"] == 2
    assert captured["fallback_languages"] == ("en",)
    assert payload == {
        "video_id": "abcdefghijk",
        "language": "auto",
        "transcript_text": "fallback",
    }


def test_transcript_client_rejects_non_positive_timeout() -> None:
    with pytest.raises(ValueError, match="request_timeout_seconds"):
        transcript_client.TranscriptClient(request_timeout_seconds=0)
