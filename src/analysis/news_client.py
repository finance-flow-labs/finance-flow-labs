"""RSS feed client for macro-economic news and official institution announcements."""

from __future__ import annotations

import feedparser

NEWS_FEEDS: dict[str, str] = {
    "global_macro": "https://feeds.reuters.com/reuters/businessNews",
    "us_economy": "https://feeds.reuters.com/reuters/economicNews",
    "korea_economy": "https://feeds.koreaherald.com/xml/syndication/koreaherald_all.xml",
    "fed_policy": "https://www.federalreserve.gov/feeds/press_all.xml",
    "markets": "https://feeds.reuters.com/reuters/financialNews",
}

OFFICIAL_FEEDS: dict[str, str] = {
    "us_treasury": "https://home.treasury.gov/system/files/rss/PressReleases.xml",
    "fed_monetary": "https://www.federalreserve.gov/feeds/press_monetary.xml",
    "fed_speeches": "https://www.federalreserve.gov/feeds/speeches.xml",
    "imf_news": "https://www.imf.org/en/News/rss",
    "worldbank": "https://blogs.worldbank.org/rss.xml",
    "bea_releases": "https://apps.bea.gov/rss/latest_release_rss.xml",
    "bls_releases": "https://www.bls.gov/feed/bls_latest_numbers.rss",
    "bok_news": "https://www.bok.or.kr/eng/bbs/E0000634/list.do?menuNo=400069",
}

_ALL_FEEDS = {**NEWS_FEEDS, **OFFICIAL_FEEDS}


class NewsClient:
    """Fetches RSS entries for a named news or official-institution feed."""

    def fetch(self, category: str, limit: int = 5) -> list[dict[str, object]]:
        """Return up to *limit* recent entries for *category*.

        Args:
            category: Key from NEWS_FEEDS or OFFICIAL_FEEDS.
            limit: Maximum number of entries to return.

        Returns:
            List of dicts with keys: title, link, published, summary.

        Raises:
            ValueError: If *category* is not a known feed key.
        """
        if category not in _ALL_FEEDS:
            raise ValueError(
                f"Unknown category {category!r}. "
                f"Valid options: {sorted(_ALL_FEEDS)}"
            )

        url = _ALL_FEEDS[category]
        feed = feedparser.parse(url)
        results = []
        for entry in feed.entries[:limit]:
            results.append(
                {
                    "title": entry.get("title", ""),
                    "link": entry.get("link", ""),
                    "published": entry.get("published", ""),
                    "summary": entry.get("summary", ""),
                }
            )
        return results

    @staticmethod
    def categories() -> dict[str, list[str]]:
        """Return available category names grouped by type."""
        return {
            "news": sorted(NEWS_FEEDS),
            "official": sorted(OFFICIAL_FEEDS),
        }
