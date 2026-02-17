import json
from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from uuid import uuid4
from typing import Optional, Protocol, cast

import psycopg2


class CursorProtocol(Protocol):
    description: list[tuple[str]]

    def execute(self, sql: str, params: tuple[object, ...]) -> None: ...

    def fetchall(self) -> list[tuple[object, ...]]: ...

    def fetchone(self) -> Optional[tuple[object, ...]]: ...

    def close(self) -> None: ...


class ConnectionProtocol(Protocol):
    def cursor(self) -> CursorProtocol: ...

    def commit(self) -> None: ...

    def close(self) -> None: ...


class PostgresRepository:
    def __init__(
        self,
        dsn: str = "",
        connection_factory: Optional[Callable[[], ConnectionProtocol]] = None,
    ) -> None:
        self._dsn: str = dsn
        self._connection_factory: Optional[Callable[[], ConnectionProtocol]] = (
            connection_factory
        )

    def _connect(self) -> ConnectionProtocol:
        if self._connection_factory is not None:
            return self._connection_factory()
        if not self._dsn:
            raise ValueError("dsn is required when no connection_factory is provided")
        return cast(
            ConnectionProtocol,
            cast(object, psycopg2.connect(self._dsn)),
        )

    def write_run_history(self, run: Mapping[str, object]) -> None:
        conn: ConnectionProtocol = self._connect()
        cursor: CursorProtocol = conn.cursor()
        cursor.execute(
            """
            INSERT INTO ingestion_runs(
                run_id,
                started_at,
                finished_at,
                source_name,
                status,
                raw_written,
                canonical_written,
                quarantined,
                error_message
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                run["run_id"],
                run["started_at"],
                run["finished_at"],
                run["source_name"],
                run["status"],
                run["raw_written"],
                run["canonical_written"],
                run["quarantined"],
                run["error_message"],
            ),
        )
        conn.commit()
        cursor.close()
        conn.close()

    def write_raw(self, row: Mapping[str, object]) -> None:
        conn: ConnectionProtocol = self._connect()
        cursor: CursorProtocol = conn.cursor()

        now = datetime.now(timezone.utc)
        cursor.execute(
            """
            INSERT INTO raw_event_store(
                source,
                entity_id,
                as_of,
                available_at,
                ingested_at,
                lineage_id,
                schema_version,
                license_tier,
                payload
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
            """,
            (
                str(row.get("source", "unknown")),
                str(row.get("entity_id", "unknown")),
                now,
                now,
                now,
                str(row.get("lineage_id", uuid4())),
                str(row.get("schema_version", "v1")),
                str(row.get("license_tier", "gold")),
                json.dumps(dict(row), default=str),
            ),
        )
        conn.commit()
        cursor.close()
        conn.close()

    def write_canonical(self, row: Mapping[str, object]) -> None:
        conn: ConnectionProtocol = self._connect()
        cursor: CursorProtocol = conn.cursor()

        now = datetime.now(timezone.utc)
        cursor.execute(
            """
            INSERT INTO canonical_fact_store(
                source,
                entity_id,
                as_of,
                available_at,
                ingested_at,
                license_tier,
                lineage_id,
                metric_name,
                metric_value,
                schema_version
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                str(row.get("source", "unknown")),
                str(row.get("entity_id", "unknown")),
                now,
                now,
                now,
                str(row.get("license_tier", "gold")),
                str(row.get("lineage_id", uuid4())),
                "pipeline_events",
                1,
                str(row.get("schema_version", "v1")),
            ),
        )
        conn.commit()
        cursor.close()
        conn.close()

    def write_quarantine(self, reason: str, payload: Mapping[str, object]) -> None:
        conn: ConnectionProtocol = self._connect()
        cursor: CursorProtocol = conn.cursor()

        cursor.execute(
            """
            INSERT INTO quarantine_batches(batch_id, reason, payload)
            VALUES (%s, %s, %s::jsonb)
            """,
            (str(uuid4()), reason, json.dumps(dict(payload), default=str)),
        )
        conn.commit()
        cursor.close()
        conn.close()

    def read_latest_runs(self, limit: int = 20) -> list[dict[str, object]]:
        conn: ConnectionProtocol = self._connect()
        cursor: CursorProtocol = conn.cursor()
        cursor.execute(
            """
            SELECT run_id, status, finished_at
            FROM ingestion_runs
            ORDER BY finished_at DESC
            LIMIT %s
            """,
            (limit,),
        )
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        cursor.close()
        conn.close()
        return [dict(zip(columns, row)) for row in rows]

    def read_status_counters(self) -> dict[str, int]:
        conn: ConnectionProtocol = self._connect()
        cursor: CursorProtocol = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM raw_event_store", ())
        raw_row = cursor.fetchone() or (0,)

        cursor.execute("SELECT COUNT(*) FROM canonical_fact_store", ())
        canonical_row = cursor.fetchone() or (0,)

        cursor.execute("SELECT COUNT(*) FROM quarantine_batches", ())
        quarantine_row = cursor.fetchone() or (0,)

        cursor.close()
        conn.close()

        def to_int(value: object) -> int:
            if isinstance(value, bool):
                return int(value)
            if isinstance(value, int):
                return value
            if isinstance(value, float):
                return int(value)
            if isinstance(value, str):
                return int(value)
            return 0

        return {
            "raw_events": to_int(raw_row[0]),
            "canonical_events": to_int(canonical_row[0]),
            "quarantine_events": to_int(quarantine_row[0]),
        }

    def snapshot_counts(self) -> dict[str, int]:
        return self.read_status_counters()
