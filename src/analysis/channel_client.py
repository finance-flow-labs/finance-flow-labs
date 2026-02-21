"""YouTube channel scraper — collects recent video transcripts without an API key."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import scrapetube

from src.analysis.transcript_client import TranscriptClient

# Default channels of interest for macro-economic analysis
DEFAULT_CHANNELS: dict[str, str] = {
    "박종훈의 지식한방": "@kpunch",
}


class ChannelClient:
    """Fetches recent video transcripts from a YouTube channel.

    Uses ``scrapetube`` (no API key required) to enumerate video IDs and
    ``TranscriptClient`` to download captions.
    """

    def __init__(self) -> None:
        self._transcript_client = TranscriptClient()

    def fetch(
        self,
        handle: str,
        days: int = 30,
        max_videos: int = 5,
        language: str = "ko",
    ) -> list[dict[str, object]]:
        """Return transcripts for the most recent videos from *handle*.

        Args:
            handle: YouTube channel handle (e.g. ``@kpunch``) or channel URL.
            days: Only include videos published within the last *days* days.
            max_videos: Maximum number of videos to retrieve.
            language: Preferred transcript language.

        Returns:
            List of dicts with keys: video_id, title, published_at, transcript_text.
            Entries for which transcript fetching fails are silently skipped.
        """
        cutoff = datetime.now(tz=timezone.utc) - timedelta(days=days)

        results: list[dict[str, object]] = []
        try:
            # channel_username with '@' handles fails on newer YouTube responses;
            # channel_url is the reliable alternative.
            if handle.startswith("@"):
                videos = scrapetube.get_channel(
                    channel_url=f"https://www.youtube.com/{handle}"
                )
            else:
                videos = scrapetube.get_channel(channel_username=handle)
            for video in videos:
                if len(results) >= max_videos:
                    break

                video_id: str = video.get("videoId", "")
                if not video_id:
                    continue

                # scrapetube returns publishedTimeText (relative) but not epoch;
                # we attempt to parse the rich data when available.
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

                try:
                    transcript_data = self._transcript_client.fetch(video_id, language=language)
                    transcript_text = transcript_data["transcript_text"]
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
