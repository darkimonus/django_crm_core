# Test Data

This directory contains curated datasets used to exercise the CRM core with realistic inputs across value kinds, SCD2 transitions, error scenarios, and performance. For how to run management commands with these files, see MANAGEMENT_COMMANDS.md.

## File Overview

### 📁 Basic Test Files

#### sample_entities.json
- Purpose: Basic entity testing
- Content: 5 entities (3 PERSON, 2 COMPANY)
- Records: 5
- Notes: Focused on entity create path.

#### sample_details.json
- Purpose: Basic detail testing with all value types
- Content: 15 details covering TEXT, NUM, TS, BOOL, JSON
- Records: 15
- Notes: Attaches to a single entity for easier inspection.

### 📁 Advanced Test Files

#### combined_data.json
- Purpose: Mixed entities and details
- Content: 2 entities + 5 details
- Records: 7
- Notes: Validates mixed ingestion flows in one run.

#### large_dataset.jsonl
- Purpose: Performance and batch processing
- Content: 10 entities + 20 details (JSONL)
- Records: 30
- Notes: Streaming-friendly; suited for batch-size and throughput checks.

### 📁 Error Testing Files

#### invalid_data.json
- Purpose: Negative scenarios and validation
- Content: 5 intentionally invalid records
- Notes: Unknown types, invalid kinds, missing fields, bad timestamps.

#### update_scenarios.json
- Purpose: SCD2 update behavior
- Content: Updates over time for the same entity + details
- Records: 8
- Notes: Demonstrates version open/close and idempotency.

## How to Use These Files

See MANAGEMENT_COMMANDS.md for usage of `load_entity_types`, `batch_ingest`, and `snapshot_refresh`. Use file paths from this folder (e.g., `test_data/sample_entities.json`) as inputs to those commands.

## Data Types Covered

### Entity Types
- PERSON: Individual people
- COMPANY: Business entities

### Detail Value Kinds
- TEXT: String values (emails, names, etc.)
- NUM: Numeric values (ages, salaries, counts)
- TS: Timestamp values (dates, times)
- BOOL: Boolean values (true/false flags)
- JSON: Structured data

### Common Detail Codes
- EMAIL, PHONE, WEBSITE, AGE, SALARY, EMPLOYEE_COUNT
- BIRTH_DATE, FOUNDED_DATE, IS_ACTIVE, IS_PUBLIC
- DEPARTMENT, ROLE, INDUSTRY, SECTOR, MARKET_CAP
- SCORE, REVENUE, PREFERENCES (JSON), FUNDING_ROUNDS (JSON), METRICS (JSON)

## Test Scenarios Covered by Files

1) Basic functionality: entity/detail creation across all value kinds, mixed single-file loads.
2) Performance: JSONL, larger volumes, suitability for varying batch sizes.
3) Error handling: invalid records and partial progress behavior.
4) SCD2: initial creation, updates, idempotency, version history.
5) Audit trail: actor, correlation_id, timestamped changes.

## Correlation IDs in Files

- test_batch_001: Basic sample data
- test_combined_001: Combined data
- large_batch_001: Large dataset
- invalid_test_001: Invalid data
- update_test_001/002/003: Update scenarios over time

## Expected Behaviors When Ingested

- Successful runs: entities/details created or updated; audit trail records before/after; ingest statistics reported.
- Error runs: invalid records rejected; errors logged; totals include error counts (behavior depends on continue-on-error).
- SCD2 updates: new versions opened, current versions closed; hashdiff changes tracked.

## Tips for Working With These Datasets

1) Start with sample_* files before moving to large_dataset.jsonl.
2) Use correlation IDs to trace and debug specific runs.
3) Validate SCD2 transitions using update_scenarios.json.
4) Use invalid_data.json to exercise error paths and logging.
