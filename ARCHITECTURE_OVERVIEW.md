Architecture Overview

This project implements a Django-based CRM core with SCD Type 2 (SCD2) versioning integrated in-table.

Key components

- cockpit/: Django project configuration (settings, URLs) and Makefile integration.
- crm/: CRM application with models, API (DRF), services (SCD2 upserts, ingest, audit), and management commands.
- test_data/: Sample JSON/JSONL files for batch ingest and demos.

Core data model (SCD2)

- Entity: Versioned in place by SCD2 columns `valid_from`, `valid_to`, `is_current`, with exclusion constraint to prevent overlapping versions per `entity_uuid`. Partial unique index ensures a single current row.
- EntityType: Reference table for entity types (e.g., PERSON, COMPANY).
- EntityDetail: Versioned details keyed by `(entity_uuid, detail_code)` with SCD2 columns and overlap exclusion per pair; supports typed values via `value_kind` and `value_*` columns and idempotency via `hashdiff`.

Services and semantics

- SCD2 upserts: `crm/services/scd2/` provides `upsert_entity` and `upsert_entity_detail`; operations are idempotent by hashdiff and perform close-and-open transitions. Audit events are written on changes.
- Ingestion: `crm/services/ingest.py` wraps upsert functions for batch and real-time entry points.
- Audit: Centralized audit log captures who/when/what changed.

API surface (DRF)

- `GET /api/v1/entities`: List current entities, filterable (type, details), optional `include_details=1`.
- `GET /api/v1/entities/{entity_uuid}`: Current snapshot with details.
- `POST /api/v1/entities`: Create first version (requires auth).
- `PATCH /api/v1/entities/{entity_uuid}`: SCD2 update (requires auth).
- `GET /api/v1/entities-asof?as_of=ISO8601`: As-of snapshot with optional details.
- `GET /api/v1/diff?from=ISO8601&to=ISO8601`: Audit events in range.

Constraints & indexing

- Database-first constraints: GiST exclusion constraints for intervals; partial unique indexes for current rows; covering indexes for common filters.

Extensibility

- Modular services and APIs with shared SCD2 semantics allow other modules to plug in (e.g., risk, compliance).


Performance Notes

- See PERFORMANCE.md for:
  - Indexing strategy for current, as-of, and diff queries.
  - Example SQL and EXPLAIN plans for common endpoints.
  - Tips on leveraging the GiST range index used by SCD2 constraints for as-of lookups.

PII Handling

- See PII_GUIDELINES.md for:
  - Data classification and minimization guidance.
  - Optional field-level protections (hashing/encryption) and audit redaction patterns.
  - Access control, retention, and test data practices.
