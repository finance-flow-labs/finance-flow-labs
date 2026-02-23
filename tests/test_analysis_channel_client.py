from __future__ import annotations

import src.analysis.channel_client as channel_client
from youtube_transcript_api import IpBlocked


def _video(video_id: str, published_at: str = "1 day ago") -> dict[str, object]:
    return {
        "videoId": video_id,
        "title": {"runs": [{"text": f"title-{video_id}"}]},
        "publishedTimeText": {"simpleText": published_at},
    }


def test_channel_fetch_respects_explicit_max_attempts(monkeypatch) -> None:
    videos = [_video(f"v-{idx}") for idx in range(30)]
    captured_limit: dict[str, int] = {}

    def fake_get_channel(**kwargs):
        captured_limit["value"] = int(kwargs["limit"])
        return iter(videos)

    monkeypatch.setattr(channel_client.scrapetube, "get_channel", fake_get_channel)

    class AlwaysFailTranscriptClient:
        def __init__(self) -> None:
            self.calls: list[str] = []

        def fetch(self, video_id: str, language: str = "ko") -> dict[str, object]:
            self.calls.append(video_id)
            raise RuntimeError("transcript fetch failed")

    transcript_client = AlwaysFailTranscriptClient()
    client = channel_client.ChannelClient(transcript_client=transcript_client)  # type: ignore[arg-type]

    results = client.fetch("@kpunch", max_videos=3, max_attempts=5)

    assert results == []
    assert captured_limit["value"] == 5
    assert len(transcript_client.calls) == 5


def test_channel_fetch_stops_immediately_on_ip_blocked(monkeypatch) -> None:
    videos = [_video("v-1"), _video("v-2"), _video("v-3")]

    def fake_get_channel(**kwargs):
        return iter(videos)

    monkeypatch.setattr(channel_client.scrapetube, "get_channel", fake_get_channel)

    class BlockedTranscriptClient:
        def __init__(self) -> None:
            self.calls = 0

        def fetch(self, video_id: str, language: str = "ko") -> dict[str, object]:
            self.calls += 1
            raise IpBlocked(video_id)

    transcript_client = BlockedTranscriptClient()
    client = channel_client.ChannelClient(transcript_client=transcript_client)  # type: ignore[arg-type]

    results = client.fetch("@kpunch", max_videos=3, max_attempts=10)

    assert results == []
    assert transcript_client.calls == 1


def test_channel_fetch_applies_days_filter_for_parseable_relative_time(monkeypatch) -> None:
    videos = [
        _video("old-en", "40 days ago"),
        _video("old-ko", "2개월 전"),
        _video("new-en", "3 days ago"),
        _video("new-ko", "12시간 전"),
    ]

    def fake_get_channel(**kwargs):
        return iter(videos)

    monkeypatch.setattr(channel_client.scrapetube, "get_channel", fake_get_channel)

    class SuccessTranscriptClient:
        def __init__(self) -> None:
            self.calls: list[str] = []

        def fetch(self, video_id: str, language: str = "ko") -> dict[str, object]:
            self.calls.append(video_id)
            return {"transcript_text": f"text-{video_id}"}

    transcript_client = SuccessTranscriptClient()
    client = channel_client.ChannelClient(transcript_client=transcript_client)  # type: ignore[arg-type]

    results = client.fetch("@kpunch", days=30, max_videos=5, max_attempts=10)

    assert [item["video_id"] for item in results] == ["new-en", "new-ko"]
    assert transcript_client.calls == ["new-en", "new-ko"]


def test_channel_fetch_uses_bounded_default_max_attempts(monkeypatch) -> None:
    videos = [_video(f"v-{idx}") for idx in range(100)]
    captured_limit: dict[str, int] = {}

    def fake_get_channel(**kwargs):
        captured_limit["value"] = int(kwargs["limit"])
        return iter(videos)

    monkeypatch.setattr(channel_client.scrapetube, "get_channel", fake_get_channel)

    class AlwaysFailTranscriptClient:
        def __init__(self) -> None:
            self.calls: list[str] = []

        def fetch(self, video_id: str, language: str = "ko") -> dict[str, object]:
            self.calls.append(video_id)
            raise RuntimeError("transcript fetch failed")

    transcript_client = AlwaysFailTranscriptClient()
    client = channel_client.ChannelClient(transcript_client=transcript_client)  # type: ignore[arg-type]

    results = client.fetch("@kpunch", max_videos=2)

    assert results == []
    assert captured_limit["value"] == 10
    assert len(transcript_client.calls) == 10
