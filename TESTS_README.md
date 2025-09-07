Tests Overview

This project uses pytest with Django settings configured in `cockpit/config/settings_test.py`.
All tests for the CRM app live under `cockpit/crm/tests/` and cover services (SCD2 + ingest), API endpoints, and model constraints.

Running tests via Makefile

```bash
 make test
 ```
- Runs all tests for the CRM app (alias: `make test-all`).
  Example: make test
```bash
make test-all
```
- Same as `make test`; runs the full suite under `cockpit/crm/tests`.
  Example: make test-all
```bash
make test-services
```
- Runs only service-layer tests (SCD2 transitions, ingest wrappers).
  Example: make test-services
```bash
make test-api
```
- Runs only API tests (entity create/update/list/history, as-of snapshot, diff).
  Example: make test-api
```bash
make test-models
```
- Runs model constraint and negative tests (exclusion constraints, uniqueness).
  Example: make test-models

Notes

- All Makefile commands execute pytest inside the app container and pass the proper Django settings.
- If you prefer running locally, you can execute: `pytest cockpit/crm --ds=cockpit.config.settings_test`.
- Test data samples for batch ingestion are in `cockpit/test_data/`; see `MANAGEMENT_COMMANDS.md` for ingestion examples.

Test index and purpose (all 23 tests)

Services (SCD2 + ingest)

- test_scd2.test_entity_create_and_noop: upsert_entity creates first version then no-ops on identical payload.
- test_scd2.test_entity_update_and_backdated_error: update advances version; backdated change raises BackdatedIntervalError.
- test_scd2.test_invalid_type_code: upsert_entity with unknown type raises TypeCodeNotFound.
- test_ingest.test_ingest_entity_idempotent: ingest_entity idempotency for identical payloads.
- test_ingest.test_ingest_detail_create_and_noop: ingest_detail creates detail then no-ops on identical replay.
- test_exceptions.test_type_code_not_found: ingest_entity surfaces TypeCodeNotFound for unknown type.

API (create, update, list, as-of, diff, auth)

- TestEntityAPI.test_create_and_retrieve_with_details: POST creates entity+detail; GET returns entity with current details.
- TestEntityAPI.test_patch_and_filters: PATCH updates display_name and adds a detail; verifies list include_details and detail filters.
- TestEntityAPI.test_asof_and_diff: Smoke for as-of and diff endpoints with valid params.
- TestAuthAPI.test_unauthenticated_writes_blocked: POST without auth is rejected (401/403).
- TestFiltersAPI.test_search_and_type_filter: search by display_name fragment and type filter return expected results.
- TestFiltersAPI.test_detail_presence_and_bool_value: presence-only filter on detail_code and BOOL typed filter work.
- TestAsOfAPI.test_missing_asof_param_400: missing as_of produces 400 validation error.
- TestAsOfAPI.test_asof_with_details_truthy_parse: include_details truthy parsing (“yes”) returns details valid at as_of.
- TestDiffAPI.test_diff_groups_entity_and_detail_changes: diff groups both entity field and detail changes; unified values present.
- TestIdempotencyAPI.test_patch_idempotency_same_payload: replaying same PATCH is a no-op (no extra versions created).

Models (constraints and checks)

- test_entities_negative.test_entity_unique_current_violation: unique current row per entity_uuid enforced.
- test_entities_negative.test_entity_overlap_exclusion: overlap exclusion for non-current windows enforced.
- test_entity_checks.test_entity_current_must_have_valid_to_null: current rows must have valid_to NULL.
- test_entity_checks.test_entity_valid_bounds_if_not_null: if valid_to set (non-current), it must be > valid_from.
- test_entitydetail_constraints.test_detail_unique_current_violation: unique current row per (entity_uuid, detail_code) enforced.
- test_entitydetail_constraints.test_detail_overlap_exclusion: overlap exclusion per (entity_uuid, detail_code) enforced.
- test_entitydetail_constraints.test_detail_kind_checks: value_kind-specific NOT NULL checks (TEXT/NUM/TS/BOOL/JSON) enforced.
