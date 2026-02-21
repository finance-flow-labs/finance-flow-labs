"""Official document fetcher with domain whitelist and HTML stripping."""

from __future__ import annotations

import urllib.parse
import urllib.request
from html.parser import HTMLParser

ALLOWED_DOMAINS: frozenset[str] = frozenset(
    {
        "federalreserve.gov",
        "treasury.gov",
        "imf.org",
        "worldbank.org",
        "bis.org",
        "bok.or.kr",
        "moef.go.kr",
        "bea.gov",
        "bls.gov",
    }
)


class _TextExtractor(HTMLParser):
    """Minimal HTML parser that collects visible text."""

    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []
        self._skip = False

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag in {"script", "style", "nav", "footer", "header"}:
            self._skip = True

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "nav", "footer", "header"}:
            self._skip = False

    def handle_data(self, data: str) -> None:
        if not self._skip:
            stripped = data.strip()
            if stripped:
                self._parts.append(stripped)

    def text(self) -> str:
        return "\n".join(self._parts)


class DocumentClient:
    """Fetches and extracts plain text from whitelisted official document URLs."""

    def fetch(self, url: str, max_chars: int = 4000) -> dict[str, object]:
        """Fetch *url*, strip HTML, and return truncated plain text.

        Args:
            url: Must belong to an ALLOWED_DOMAINS domain.
            max_chars: Maximum characters of extracted text to return.

        Returns:
            Dict with keys: url, content (str), char_count (int).

        Raises:
            ValueError: If the URL domain is not in ALLOWED_DOMAINS.
        """
        parsed = urllib.parse.urlparse(url)
        hostname = parsed.hostname or ""
        # Match on base domain (e.g. "www.federalreserve.gov" → "federalreserve.gov")
        base_domain = ".".join(hostname.split(".")[-2:]) if "." in hostname else hostname
        if base_domain not in ALLOWED_DOMAINS:
            raise ValueError(
                f"Domain {hostname!r} is not in the allowed list. "
                f"Allowed: {sorted(ALLOWED_DOMAINS)}"
            )

        req = urllib.request.Request(
            url,
            headers={"User-Agent": "FinanceFlowLabs/1.0 (macro-analysis research bot)"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw_html = resp.read().decode("utf-8", errors="replace")

        parser = _TextExtractor()
        parser.feed(raw_html)
        text = parser.text()[:max_chars]

        return {
            "url": url,
            "content": text,
            "char_count": len(text),
        }
