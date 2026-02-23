"""YouTube channel scraper — collects recent video transcripts without an API key."""

from __future__ import annotations

import re

import scrapetube
from youtube_transcript_api import IpBlocked, RequestBlocked

from src.analysis.transcript_client import TranscriptClient

# Default channels of interest for macro-economic analysis
DEFAULT_CHANNELS: dict[str, str] = {
    "박종훈의 지식한방": "@kpunch",
}

_DEFAULT_ATTEMPT_MULTIPLIER = 4
_MIN_MAX_ATTEMPTS = 10
_MAX_MAX_ATTEMPTS = 50

_EN_DAYS_BY_UNIT = {
    "minute": 1 / 1440,
    "minutes": 1 / 1440,
    "hour": 1 / 24,
    "hours": 1 / 24,
    "day": 1,
    "days": 1,
    "week": 7,
    "weeks": 7,
    "month": 30,
    "months": 30,
    "year": 365,
    "years": 365,
}

_KO_DAYS_BY_UNIT = {
    "분": 1 / 1440,
    "시간": 1 / 24,
    "일": 1,
    "주": 7,
    "개월": 30,
    "년": 365,
}

_EN_RELATIVE_TIME_PATTERN = re.compile(
    r"(?P<value>\d+)\s*(?P<unit>minute|minutes|hour|hours|day|days|week|weeks|month|months|year|years)\s+ago"
)

_KO_RELATIVE_TIME_PATTERN = re.compile(
    r"(?P<value>\d+)\s*(?P<unit>분|시간|일|주|개월|년)\s*전"
)


class ChannelClient:
    """Fetches recent video transcripts from a YouTube channel.

    Uses ``scrapetube`` (no API key required) to enumerate video IDs and
    ``TranscriptClient`` to download captions.
    """

    def __init__(self, transcript_client: TranscriptClient | None = None) -> None:
        self._transcript_client = transcript_client or TranscriptClient()

    def fetch(
        self,
        handle: str,
        days: int = 30,
        max_videos: int = 5,
        language: str = "ko",
        max_attempts: int | None = None,
    ) -> list[dict[str, object]]:
        """Return transcripts for the most recent videos from *handle*.

        Args:
            handle: YouTube channel handle (e.g. ``@kpunch``) or channel URL.
            days: Only include videos published within the last *days* days.
            max_videos: Maximum number of videos to retrieve.
            language: Preferred transcript language.
            max_attempts: Maximum number of transcript attempts across videos.
                          If omitted, uses a bounded default based on ``max_videos``.

        Returns:
            List of dicts with keys: video_id, title, published_at, transcript_text.
            Entries for which transcript fetching fails are skipped.

        Notes:
            - If YouTube blocks transcript access (IpBlocked/RequestBlocked),
              fetching stops early to avoid long hangs.
            - ``published_at`` filtering is best-effort because YouTube returns
              relative text in mixed locales.
        """
        if days <= 0:
            raise ValueError("days must be > 0")
        if max_videos <= 0:
            raise ValueError("max_videos must be > 0")

        attempts_cap = max_attempts
        if attempts_cap is None:
            attempts_cap = _recommended_max_attempts(max_videos)
        if attempts_cap <= 0:
            raise ValueError("max_attempts must be > 0")

        results: list[dict[str, object]] = []
        attempts = 0

        try:
            # channel_username with '@' handles fails on newer YouTube responses;
            # channel_url is the reliable alternative.
            if handle.startswith("@"):
                videos = scrapetube.get_channel(
                    channel_url=f"https://www.youtube.com/{handle}",
                    limit=attempts_cap,
                )
            else:
                videos = scrapetube.get_channel(
                    channel_username=handle,
                    limit=attempts_cap,
                )

            for video in videos:
                if len(results) >= max_videos or attempts >= attempts_cap:
                    break

                video_id: str = video.get("videoId", "")
                if not video_id:
                    continue

                # scrapetube returns publishedTimeText (relative) but not epoch;
                # we attempt to parse the relative text when available.
                title: str = ""
                published_at: str = ""
                try:
                    title = (
                        video.get("title", {})
                        .get("runs", [{}])[0]
                        .get("text", "")
                    )
                    published_at = video.get("publishedTimeText", {}).get("simpleText", "")
                except Exception:
                    pass

                if not _is_within_days(published_at, days=days):
                    continue

                attempts += 1
                try:
                    transcript_data = self._transcript_client.fetch(video_id, language=language)
                    transcript_text = transcript_data["transcript_text"]
                except (IpBlocked, RequestBlocked):
                    break
                except Exception:
                    continue

                results.append(
                    {
                        "video_id": video_id,
                        "title": title,
                        "published_at": published_at,
                        "transcript_text": transcript_text,
                    }
                )
        except Exception:
            pass

        return results


def _recommended_max_attempts(max_videos: int) -> int:
    """Return bounded default attempt count from desired output size."""
    return max(
        _MIN_MAX_ATTEMPTS,
        min(_MAX_MAX_ATTEMPTS, max_videos * _DEFAULT_ATTEMPT_MULTIPLIER),
    )


def _is_within_days(published_at: str, days: int) -> bool:
    """Return whether relative ``published_at`` appears within ``days``.

    Unknown/unsupported formats are treated as in-range so we do not accidentally
    drop valid data because of locale formatting quirks.
    """
    age_days = _parse_relative_age_days(published_at)
    if age_days is None:
        return True
    return age_days <= days


def _parse_relative_age_days(published_at: str) -> float | None:
    """Best-effort parser for YouTube relative time text (EN/KO)."""
    text = published_at.strip().lower()
    if not text:
        return None

    if any(token in text for token in ("just now", "today", "방금 전", "오늘")):
        return 0.0
    if "yesterday" in text or "어제" in text:
        return 1.0

    english_match = _EN_RELATIVE_TIME_PATTERN.search(text)
    if english_match:
        value = int(english_match.group("value"))
        unit = english_match.group("unit")
        return value * _EN_DAYS_BY_UNIT[unit]

    korean_match = _KO_RELATIVE_TIME_PATTERN.search(text)
    if korean_match:
        value = int(korean_match.group("value"))
        unit = korean_match.group("unit")
        return value * _KO_DAYS_BY_UNIT[unit]

    return None
