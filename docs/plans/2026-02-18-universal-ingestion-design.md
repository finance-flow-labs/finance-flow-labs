# Universal Ingestion Design (KR+US)

Date: 2026-02-18
Scope: Research-assist workflow (no auto-trading), KR+US markets

## 1) Goal and Boundary

Build a data platform that maximizes decision quality while controlling legal, operational, and cost risk.

- v1 policy: Hybrid ingestion (selected)
- Use-case: macro -> sector -> stock analysis support
- Not in v1: order execution, fully automated trading decisions

## 2) Approach Options and Decision

### Option A: Collect-all and retain forever
- Pros: maximal coverage
- Cons: legal risk, cost explosion, schema drift, low signal density

### Option B: Hybrid (selected)
- Gold sources retained permanently
- Silver/Bronze sources cached with TTL and on-demand refetch
- Pros: high value density, controlled risk, scalable expansion

### Option C: Minimal-only
- Pros: smallest ops burden
- Cons: slower research iteration, lower exploratory power

Decision: Option B (Hybrid)

## 3) Source Tiering

### Gold (permanent)
- KR: OpenDART, ECOS, KOSIS (core series)
- US: SEC EDGAR, FRED/ALFRED, BEA/BLS (core series)

### Silver (TTL cache)
- FMP and other commercial vendors for convenience and breadth
- Retention: raw 180 days, normalized facts 24 months

### Bronze (on-demand)
- Sources with unstable legal/operational posture or low value density
- Retention: 30-90 days

## 4) Data Model and Storage Layers

Use four logical layers:

1. raw_event_store (append-only)
2. canonical_fact_store (normalized, analysis-ready)
3. point_in_time_view (backtest-safe projections)
4. cache_store (TTL-managed data)

Required metadata on every record:
- source
- entity_id
- as_of
- available_at
- ingested_at
- lineage_id
- schema_version
- license_tier

## 5) Revision-Safe Rules

- Never overwrite corrected facts in place
- Store corrections as new rows with supersession markers
- Enforce point-in-time rule: available_at <= decision_time
- Idempotency key: source + entity_id + as_of + vendor_revision_id
- If same idempotency key and same payload hash: no-op
- If same idempotency key and different payload hash: add revision row

## 6) Quality, Compliance, and Cost Gates

### Ingestion admission gates
- Legal score >= 3
- Reliability score >= 3
- Otherwise deferred regardless of total score

### Runtime checks per batch
- freshness
- completeness
- schema drift
- license policy

Failure policy:
- Block promotion to canonical_fact_store
- Route failed batches to quarantine tables

### Budget control
- Monthly cost cap enforced
- New source onboarding auto-frozen when cap is breached

## 7) Orchestration and Failure Handling

- Gold pipelines run on fixed schedule + event triggers
- Silver/Bronze pipelines are demand-aware and budget-aware
- Backfill jobs run in isolated windows and write immutable batch manifests
- Retries are bounded and idempotent
- Dead-letter queues for non-recoverable failures

## 8) Testing and Acceptance Criteria

v1 is accepted only if all pass:

- Point-in-time replay returns deterministic results for sampled dates
- Revision ingestion does not overwrite historical truth
- Schema drift triggers quarantine, not silent corruption
- Legal/license policy checks block forbidden datasets
- Cost cap and freeze behavior are observable and effective

## 9) v1 Practical Boundary

Ingest first:
- SEC EDGAR filings + key XBRL facts
- OpenDART disclosures + key financial fields
- FRED/ALFRED core macro series
- ECOS/KOSIS core KR macro series

Defer by default:
- Full tick-level market feeds
- Broad alternative data without clear research utility
- Unofficial scraping sources as system-of-record

## 10) Expansion Rules (v2+)

Add a new source only if:
- Priority score >= threshold (for example, 75/100)
- Measured uplift: coverage +15pp or analyst lead-time -20%
- Legal and reliability gates remain satisfied
