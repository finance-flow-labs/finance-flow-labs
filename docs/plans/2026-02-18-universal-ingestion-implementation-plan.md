# Universal Ingestion Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a hybrid KR+US ingestion platform that is revision-safe, policy-aware, and cost-controlled.

**Architecture:** Implement a four-layer data model (`raw_event_store`, `canonical_fact_store`, `point_in_time_view`, `cache_store`) with immutable raw ingestion, deterministic normalization, and point-in-time query safety. Apply legal/reliability gates before source onboarding and quality gates before canonical promotion.

**Tech Stack:** Python, PostgreSQL, SQL migrations, scheduler (cron/Airflow), pytest

---

### Task 1: Bootstrap project skeleton

**Files:**
- Create: `src/ingestion/__init__.py`
- Create: `src/ingestion/config.py`
- Create: `src/ingestion/models.py`
- Create: `src/ingestion/pipeline.py`
- Create: `tests/test_bootstrap.py`

**Step 1: Write the failing test**
- Add test that imports `src.ingestion.pipeline` and verifies module load.

**Step 2: Run test to verify it fails**
- Run: `pytest tests/test_bootstrap.py -v`

**Step 3: Write minimal implementation**
- Add empty modules and minimal settings object.

**Step 4: Run test to verify it passes**
- Run: `pytest tests/test_bootstrap.py -v`

**Step 5: Commit**
- `git add src/ingestion tests/test_bootstrap.py`
- `git commit -m "chore: bootstrap ingestion skeleton"`

### Task 2: Implement source registry and gate scoring

**Files:**
- Create: `src/ingestion/source_registry.py`
- Create: `tests/test_source_registry.py`

**Step 1: Write the failing test**
- Test scoring fields: `utility`, `reliability`, `legal`, `cost`, `maintenance`.
- Test hard gate: reject if legal < 3 or reliability < 3.

**Step 2: Run test to verify it fails**
- Run: `pytest tests/test_source_registry.py -v`

**Step 3: Write minimal implementation**
- Implement source descriptor dataclass and gate function.

**Step 4: Run test to verify it passes**
- Run: `pytest tests/test_source_registry.py -v`

**Step 5: Commit**
- `git add src/ingestion/source_registry.py tests/test_source_registry.py`
- `git commit -m "feat: add source scoring and admission gates"`

### Task 3: Add raw_event_store schema (append-only)

**Files:**
- Create: `migrations/001_raw_event_store.sql`
- Create: `tests/test_raw_event_schema.py`

**Step 1: Write the failing test**
- Validate required columns: `source`, `entity_id`, `as_of`, `available_at`, `ingested_at`, `lineage_id`, `schema_version`, `license_tier`.

**Step 2: Run test to verify it fails**
- Run: `pytest tests/test_raw_event_schema.py -v`

**Step 3: Write minimal implementation**
- Add append-only table with constraints and indexes.

**Step 4: Run test to verify it passes**
- Run: `pytest tests/test_raw_event_schema.py -v`

**Step 5: Commit**
- `git add migrations/001_raw_event_store.sql tests/test_raw_event_schema.py`
- `git commit -m "feat: create raw event store schema"`

### Task 4: Add canonical_fact_store + quarantine flow

**Files:**
- Create: `migrations/002_canonical_and_quarantine.sql`
- Create: `src/ingestion/quality_gate.py`
- Create: `tests/test_quality_gate.py`

**Step 1: Write the failing test**
- Test that failed batches route to quarantine.
- Test that passing batches are promotable to canonical.

**Step 2: Run test to verify it fails**
- Run: `pytest tests/test_quality_gate.py -v`

**Step 3: Write minimal implementation**
- Implement quality checks: freshness, completeness, schema drift, license policy.

**Step 4: Run test to verify it passes**
- Run: `pytest tests/test_quality_gate.py -v`

**Step 5: Commit**
- `git add migrations/002_canonical_and_quarantine.sql src/ingestion/quality_gate.py tests/test_quality_gate.py`
- `git commit -m "feat: add canonical promotion and quarantine"`

### Task 5: Add revision-safe upsert behavior

**Files:**
- Create: `src/ingestion/revision_store.py`
- Create: `tests/test_revision_store.py`

**Step 1: Write the failing test**
- Same idempotency key + same payload hash => no-op.
- Same idempotency key + different payload hash => new revision row.

**Step 2: Run test to verify it fails**
- Run: `pytest tests/test_revision_store.py -v`

**Step 3: Write minimal implementation**
- Implement idempotency key and revision insert rules.

**Step 4: Run test to verify it passes**
- Run: `pytest tests/test_revision_store.py -v`

**Step 5: Commit**
- `git add src/ingestion/revision_store.py tests/test_revision_store.py`
- `git commit -m "feat: implement revision-safe ingestion logic"`

### Task 6: Add point-in-time query safety

**Files:**
- Create: `src/ingestion/pit_query.py`
- Create: `tests/test_pit_query.py`

**Step 1: Write the failing test**
- Ensure query enforces `available_at <= decision_time`.
- Ensure deterministic replay for sampled dates.

**Step 2: Run test to verify it fails**
- Run: `pytest tests/test_pit_query.py -v`

**Step 3: Write minimal implementation**
- Implement PIT filter builder and query helper.

**Step 4: Run test to verify it passes**
- Run: `pytest tests/test_pit_query.py -v`

**Step 5: Commit**
- `git add src/ingestion/pit_query.py tests/test_pit_query.py`
- `git commit -m "feat: add point-in-time safe query helper"`

### Task 7: Implement TTL cache lifecycle

**Files:**
- Create: `src/ingestion/cache_policy.py`
- Create: `tests/test_cache_policy.py`

**Step 1: Write the failing test**
- Gold no-expiry, Silver TTL 180d/24m policy mapping, Bronze 30-90d.

**Step 2: Run test to verify it fails**
- Run: `pytest tests/test_cache_policy.py -v`

**Step 3: Write minimal implementation**
- Implement TTL policy resolver and expiration selector.

**Step 4: Run test to verify it passes**
- Run: `pytest tests/test_cache_policy.py -v`

**Step 5: Commit**
- `git add src/ingestion/cache_policy.py tests/test_cache_policy.py`
- `git commit -m "feat: enforce tier-based ttl cache policy"`

### Task 8: Build source adapters for v1 core set

**Files:**
- Create: `src/ingestion/adapters/sec_edgar.py`
- Create: `src/ingestion/adapters/opendart.py`
- Create: `src/ingestion/adapters/fred.py`
- Create: `src/ingestion/adapters/ecos.py`
- Create: `tests/test_adapters_contract.py`

**Step 1: Write the failing test**
- Adapter contract tests for normalized output shape.

**Step 2: Run test to verify it fails**
- Run: `pytest tests/test_adapters_contract.py -v`

**Step 3: Write minimal implementation**
- Implement contract-compliant adapters with stubbed HTTP client.

**Step 4: Run test to verify it passes**
- Run: `pytest tests/test_adapters_contract.py -v`

**Step 5: Commit**
- `git add src/ingestion/adapters tests/test_adapters_contract.py`
- `git commit -m "feat: add v1 core source adapters"`

### Task 9: Add budget guard and onboarding freeze

**Files:**
- Create: `src/ingestion/budget_guard.py`
- Create: `tests/test_budget_guard.py`

**Step 1: Write the failing test**
- On monthly cap breach, onboarding status switches to frozen.

**Step 2: Run test to verify it fails**
- Run: `pytest tests/test_budget_guard.py -v`

**Step 3: Write minimal implementation**
- Implement cost threshold checker and freeze flag state.

**Step 4: Run test to verify it passes**
- Run: `pytest tests/test_budget_guard.py -v`

**Step 5: Commit**
- `git add src/ingestion/budget_guard.py tests/test_budget_guard.py`
- `git commit -m "feat: add monthly budget freeze guard"`

### Task 10: End-to-end verification and docs

**Files:**
- Create: `docs/ingestion-runbook.md`
- Create: `tests/test_end_to_end_ingestion.py`

**Step 1: Write the failing test**
- Simulate ingest -> quality gate -> canonical promotion -> PIT query.

**Step 2: Run test to verify it fails**
- Run: `pytest tests/test_end_to_end_ingestion.py -v`

**Step 3: Write minimal implementation**
- Glue pipeline orchestration with mock adapters.

**Step 4: Run full test suite**
- Run: `pytest -v`

**Step 5: Commit**
- `git add docs/ingestion-runbook.md tests/test_end_to_end_ingestion.py src/ingestion`
- `git commit -m "feat: add end-to-end ingestion pipeline baseline"`
