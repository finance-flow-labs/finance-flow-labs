from __future__ import annotations

import os

from src.enduser.app import run_enduser_app


def main() -> None:
    dsn = os.getenv("SUPABASE_DB_URL") or os.getenv("DATABASE_URL")
    if not dsn:
        raise ValueError("SUPABASE_DB_URL or DATABASE_URL is required")
    run_enduser_app(dsn)


if __name__ == "__main__":
    main()
