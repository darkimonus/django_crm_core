# Django Management Commands

This document explains the Django management commands for CRM ingestion and snapshotting. For test instructions, see TESTS_README.md.

--dry-run: what it does

- Validates input, parses files, and computes actions.
- Prints planned work and statistics; does not write to the database.
- Still raises validation errors; safe for previews before real runs.

Entity Types Loader (load_entity_types)

- Purpose: Load/update reference `EntityType` rows from a JSON file [{code, title}, ...].
- Arguments: `file_path` (required)
- Options: `--dry-run`
- Run (one per block):
```bash
make load-entity-types file='test_data/entity_types.json'
```
```bash
make load-entity-types file='test_data/entity_types.json' args='--dry-run'
```
- JSON example:
```json
[
  {"code": "PERSON", "title": "Person"},
  {"code": "COMPANY", "title": "Company"}
]
```

Batch Ingest (batch_ingest)

- Purpose: Bulk ingest Entities and Details with SCD2 behavior and audit.
- Arguments: `file_path` (required JSON/JSONL)
- Options: `--actor`, `--correlation-id`, `--dry-run`, `--batch-size`, `--continue-on-error`
- Run examples (each is separately executable):
```bash
make batch-ingest file='test_data/sample_entities.json' args='--dry-run'
```
```bash
make batch-ingest file='test_data/sample_entities.json'
```
```bash
make batch-ingest file='test_data/sample_details.json' args='--dry-run'
```
```bash
make batch-ingest file='test_data/sample_details.json'
```
```bash
make batch-ingest file='test_data/combined_data.json' args='--dry-run'
```
```bash
make batch-ingest file='test_data/combined_data.json'
```
```bash
make batch-ingest file='test_data/large_dataset.jsonl' args='--batch-size 5 --dry-run'
```
```bash
make batch-ingest file='test_data/large_dataset.jsonl' args='--batch-size 5'
```
```bash
make batch-ingest file='test_data/invalid_data.json' args='--continue-on-error'
```
```bash
make batch-ingest file='test_data/update_scenarios.json' args='--dry-run'
```
```bash
make batch-ingest file='test_data/update_scenarios.json'
```
- Record types:
  - entity: requires entity_uuid, type_code, display_name, change_ts
  - detail: requires entity_uuid, detail_code, value_kind, change_ts (+ value)

Snapshot Refresh (snapshot_refresh)

- Purpose: Refresh “current” snapshots/materialized views (non-destructive).
- Options: `--entity-types`, `--detail-codes`, `--since`, `--dry-run`, `--force`, `--create-snapshot-table`
- Run examples (each block is standalone):
```bash
make snapshot-refresh-dry-run
```
```bash
make snapshot-refresh
```
```bash
make snapshot-refresh args='--entity-types PERSON --dry-run'
```
```bash
make snapshot-refresh args='--entity-types PERSON'
```
```bash
make snapshot-refresh args='--since 2025-01-19T00:00:00Z --dry-run'
```
```bash
make snapshot-refresh args='--since 2025-01-19T00:00:00Z'
```
```bash
make snapshot-refresh args='--force'
```
```bash
make snapshot-refresh args='--create-snapshot-table'
```

Error handling

- Batch ingest: file not found, invalid JSON, missing fields, invalid type code, backdated intervals (use `--continue-on-error` to proceed).
- Snapshot refresh: invalid timestamp, no changes (use `--force`), database errors.

Performance

- Prefer JSONL for large data; tune `--batch-size`. Always start with `--dry-run` to validate quickly.

Monitoring & logging

- Commands print progress and a final summary; logs go to Django logging as configured.
