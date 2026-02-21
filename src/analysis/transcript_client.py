"""YouTube transcript fetcher."""

from __future__ import annotations

import re

from youtube_transcript_api import YouTubeTranscriptApi


def extract_video_id(url: str) -> str:
    """Extract the YouTube video ID from a URL or bare ID string.

    Supports:
        - https://www.youtube.com/watch?v=VIDEO_ID
        - https://youtu.be/VIDEO_ID
        - https://www.youtube.com/shorts/VIDEO_ID
        - Bare 11-character ID

    Raises:
        ValueError: If no video ID can be extracted.
    """
    patterns = [
        r"[?&]v=([A-Za-z0-9_-]{11})",
        r"youtu\.be/([A-Za-z0-9_-]{11})",
        r"shorts/([A-Za-z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    # Might be a bare video ID
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", url):
        return url
    raise ValueError(f"Cannot extract YouTube video ID from: {url!r}")


class TranscriptClient:
    """Fetches transcripts for individual YouTube videos."""

    def fetch(self, url: str, language: str = "ko") -> dict[str, object]:
        """Return the transcript for *url*.

        Args:
            url: YouTube video URL or bare video ID.
            language: Preferred transcript language code ('ko' or 'en').
                      Falls back to the other language if unavailable.

        Returns:
            Dict with keys: video_id, language, transcript_text.

        Raises:
            ValueError: If the video ID cannot be extracted.
            Exception: Propagates youtube_transcript_api errors.
        """
        video_id = extract_video_id(url)

        fallback = "en" if language == "ko" else "ko"
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(
                video_id, languages=[language, fallback]
            )
            used_language = language
        except Exception:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            used_language = "auto"

        transcript_text = " ".join(entry["text"] for entry in transcript_list)

        return {
            "video_id": video_id,
            "language": used_language,
            "transcript_text": transcript_text,
        }
