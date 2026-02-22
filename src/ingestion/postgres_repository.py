import json
from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from uuid import uuid4
from typing import Optional, Protocol, cast

import psycopg2

from src.research.contracts import NormalizedSeriesPoint


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

    def write_macro_analysis_result(self, result: Mapping[str, object]) -> None:
        conn: ConnectionProtocol = self._connect()
        cursor: CursorProtocol = conn.cursor()
        cursor.execute(
            """
            INSERT INTO macro_analysis_results(
                run_id,
                as_of,
                regime,
                confidence,
                base_case,
                bull_case,
                bear_case,
                policy_case,
                critic_case,
                reason_codes,
                risk_flags,
                triggers,
                narrative,
                model
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s, %s)
            """,
            (
                result["run_id"],
                result["as_of"],
                result["regime"],
                result["confidence"],
                result["base_case"],
                result["bull_case"],
                result["bear_case"],
                result.get("policy_case", ""),
                result.get("critic_case", ""),
                json.dumps(result["reason_codes"], default=str),
                json.dumps(result["risk_flags"], default=str),
                json.dumps(result["triggers"], default=str),
                result["narrative"],
                result.get("model"),
            ),
        )
        conn.commit()
        cursor.close()
        conn.close()

    def read_latest_macro_analysis(self, limit: int = 20) -> list[dict[str, object]]:
        conn: ConnectionProtocol = self._connect()
        cursor: CursorProtocol = conn.cursor()
        cursor.execute(
            """
            SELECT
                run_id,
                as_of,
                regime,
                confidence,
                base_case,
                bull_case,
                bear_case,
                policy_case,
                critic_case,
                reason_codes,
                risk_flags,
                triggers,
                narrative,
                model,
                created_at
            FROM macro_analysis_results
            ORDER BY as_of DESC, created_at DESC
            LIMIT %s
            """,
            (limit,),
        )
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        cursor.close()
        conn.close()
        return [dict(zip(columns, row)) for row in rows]

    def write_forecast_record(self, record: Mapping[str, object]) -> int:
        conn: ConnectionProtocol = self._connect()
        cursor: CursorProtocol = conn.cursor()
        cursor.execute(
            """
            INSERT INTO forecast_records(
                thesis_id,
                horizon,
                expected_return_low,
                expected_return_high,
                expected_volatility,
                expected_drawdown,
                confidence,
                key_drivers,
                evidence_hard,
                evidence_soft,
                as_of
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s)
            RETURNING id
            """,
            (
                record["thesis_id"],
                record["horizon"],
                record["expected_return_low"],
                record["expected_return_high"],
                record.get("expected_volatility"),
                record.get("expected_drawdown"),
                record["confidence"],
                json.dumps(record.get("key_drivers", []), default=str),
                json.dumps(record.get("evidence_hard", []), default=str),
                json.dumps(record.get("evidence_soft", []), default=str),
                record["as_of"],
            ),
        )
        row = cursor.fetchone() or (0,)
        conn.commit()
        cursor.close()
        conn.close()
        return int(row[0])

    def write_realization_from_outcome(
        self,
        forecast_id: int,
        realized_return: float,
        evaluated_at: object,
        realized_volatility: Optional[float] = None,
        max_drawdown: Optional[float] = None,
    ) -> int:
        conn: ConnectionProtocol = self._connect()
        cursor: CursorProtocol = conn.cursor()

        cursor.execute(
            """
            SELECT expected_return_low, expected_return_high
            FROM forecast_records
            WHERE id = %s
            """,
            (forecast_id,),
        )
        forecast_row = cursor.fetchone()
        if forecast_row is None:
            cursor.close()
            conn.close()
            raise ValueError(f"forecast_id not found: {forecast_id}")

        expected_low = float(forecast_row[0])
        expected_high = float(forecast_row[1])
        expected_mid = (expected_low + expected_high) / 2
        forecast_error = expected_mid - realized_return
        hit = expected_low <= realized_return <= expected_high

        cursor.execute(
            """
            INSERT INTO realization_records(
                forecast_id,
                realized_return,
                realized_volatility,
                max_drawdown,
                hit,
                forecast_error,
                evaluated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                forecast_id,
                realized_return,
                realized_volatility,
                max_drawdown,
                hit,
                forecast_error,
                evaluated_at,
            ),
        )
        row = cursor.fetchone() or (0,)
        conn.commit()
        cursor.close()
        conn.close()
        return int(row[0])

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

    def write_macro_series_points(self, points: list[NormalizedSeriesPoint]) -> int:
        if not points:
            return 0

        conn: ConnectionProtocol = self._connect()
        cursor: CursorProtocol = conn.cursor()

        for point in points:
            cursor.execute(
                """
                INSERT INTO macro_series_points(
                    source,
                    entity_id,
                    metric_key,
                    as_of,
                    available_at,
                    value,
                    lineage_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    point.source,
                    point.entity_id,
                    point.metric_key,
                    point.as_of,
                    point.available_at,
                    point.value,
                    point.lineage_id,
                ),
            )

        conn.commit()
        cursor.close()
        conn.close()
        return len(points)

    def read_macro_series_points(
        self,
        metric_key: str,
        limit: int = 100,
    ) -> list[dict[str, object]]:
        conn: ConnectionProtocol = self._connect()
        cursor: CursorProtocol = conn.cursor()
        cursor.execute(
            """
            SELECT source, entity_id, metric_key, as_of, available_at, value, lineage_id
            FROM macro_series_points
            WHERE metric_key = %s
            ORDER BY as_of DESC
            LIMIT %s
            """,
            (metric_key, limit),
        )
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        cursor.close()
        conn.close()
        return [dict(zip(columns, row)) for row in rows]

    def read_canonical_facts(
        self, source: str, metric_name: str, limit: int = 12
    ) -> list[dict[str, object]]:
        """Return up to *limit* rows from canonical_fact_store ordered by as_of asc.

        Used by CanonicalDataClient in the analysis layer.
        Returns [] when no connection is configured.
        """
        conn: ConnectionProtocol = self._connect()
        cursor: CursorProtocol = conn.cursor()
        cursor.execute(
            """
            SELECT
                source,
                entity_id,
                metric_name,
                metric_value,
                as_of,
                available_at,
                ingested_at,
                lineage_id
            FROM canonical_fact_store
            WHERE source = %s AND metric_name = %s
            ORDER BY as_of DESC
            LIMIT %s
            """,
            (source, metric_name, limit),
        )
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        cursor.close()
        conn.close()
        # Return chronological order (oldest first) for anomaly detection
        return list(reversed([dict(zip(columns, row)) for row in rows]))

    def snapshot_counts(self) -> dict[str, int]:
        return self.read_status_counters()
