"""Command-line interface for the macro-analysis data tools.

Usage:
    python -m src.analysis.cli series <source> <id> [--limit N]
    python -m src.analysis.cli news <category> [--limit N]
    python -m src.analysis.cli official <institution> [--limit N]
    python -m src.analysis.cli document <url> [--max-chars N]
    python -m src.analysis.cli youtube <url> [--language ko|en]
    python -m src.analysis.cli channel <handle> [--days N] [--max-videos N]
    python -m src.analysis.cli anomaly <source> <series_id> [--window N] [--threshold F]

All subcommands output JSON to stdout.
"""

from __future__ import annotations

import argparse
import json
import sys

from src.analysis.data_client import CanonicalDataClient, detect_anomalies
from src.analysis.news_client import NewsClient
from src.analysis.document_client import DocumentClient
from src.analysis.transcript_client import TranscriptClient
from src.analysis.channel_client import ChannelClient


def cmd_series(args: argparse.Namespace) -> None:
    client = CanonicalDataClient()
    rows = client.read_series(args.source, args.id, limit=args.limit)
    print(json.dumps(rows, default=str, ensure_ascii=False, indent=2))


def cmd_news(args: argparse.Namespace) -> None:
    client = NewsClient()
    entries = client.fetch(args.category, limit=args.limit)
    print(json.dumps(entries, ensure_ascii=False, indent=2))


def cmd_official(args: argparse.Namespace) -> None:
    client = NewsClient()
    entries = client.fetch(args.institution, limit=args.limit)
    print(json.dumps(entries, ensure_ascii=False, indent=2))


def cmd_document(args: argparse.Namespace) -> None:
    client = DocumentClient()
    result = client.fetch(args.url, max_chars=args.max_chars)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_youtube(args: argparse.Namespace) -> None:
    client = TranscriptClient()
    result = client.fetch(args.url, language=args.language)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_channel(args: argparse.Namespace) -> None:
    client = ChannelClient()
    results = client.fetch(
        args.handle, days=args.days, max_videos=args.max_videos, language=args.language
    )
    print(json.dumps(results, ensure_ascii=False, indent=2))


def cmd_anomaly(args: argparse.Namespace) -> None:
    client = CanonicalDataClient()
    rows = client.read_series(args.source, args.series_id, limit=args.window * 3)
    flagged = detect_anomalies(rows, window=args.window, threshold=args.threshold)
    print(json.dumps(flagged, default=str, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m src.analysis.cli",
        description="Macro-analysis data tools. All output is JSON.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # series
    p_series = sub.add_parser("series", help="Read canonical time-series from DB")
    p_series.add_argument("source", help="Data source (e.g. fred, ecos)")
    p_series.add_argument("id", help="Series metric_name (e.g. CPIAUCSL, 722Y001)")
    p_series.add_argument("--limit", type=int, default=12)
    p_series.set_defaults(func=cmd_series)

    # news
    p_news = sub.add_parser("news", help="Fetch macro news RSS feed")
    p_news.add_argument(
        "category",
        choices=["global_macro", "us_economy", "korea_economy", "fed_policy", "markets"],
    )
    p_news.add_argument("--limit", type=int, default=5)
    p_news.set_defaults(func=cmd_news)

    # official
    p_official = sub.add_parser("official", help="Fetch official institution RSS feed")
    p_official.add_argument(
        "institution",
        choices=["fed_monetary", "fed_speeches", "ecb_press"],
    )
    p_official.add_argument("--limit", type=int, default=5)
    p_official.set_defaults(func=cmd_official)

    # document
    p_doc = sub.add_parser("document", help="Fetch and strip text from an official URL")
    p_doc.add_argument("url")
    p_doc.add_argument("--max-chars", type=int, default=4000)
    p_doc.set_defaults(func=cmd_document)

    # youtube
    p_yt = sub.add_parser("youtube", help="Fetch YouTube video transcript")
    p_yt.add_argument("url")
    p_yt.add_argument("--language", default="ko", choices=["ko", "en"])
    p_yt.set_defaults(func=cmd_youtube)

    # channel
    p_ch = sub.add_parser("channel", help="Fetch recent transcripts from a YouTube channel")
    p_ch.add_argument("handle", help="Channel handle (e.g. @kpunch)")
    p_ch.add_argument("--days", type=int, default=30)
    p_ch.add_argument("--max-videos", type=int, default=5)
    p_ch.add_argument("--language", default="ko", choices=["ko", "en"])
    p_ch.set_defaults(func=cmd_channel)

    # anomaly
    p_anom = sub.add_parser("anomaly", help="Detect anomalies in a canonical series")
    p_anom.add_argument("source", help="Data source (e.g. fred, ecos)")
    p_anom.add_argument("series_id", help="Series metric_name")
    p_anom.add_argument("--window", type=int, default=6)
    p_anom.add_argument("--threshold", type=float, default=2.0)
    p_anom.set_defaults(func=cmd_anomaly)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
