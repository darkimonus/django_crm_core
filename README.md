django_crm_core

Short description

A Django-based CRM core implementing in-table SCD Type 2 versioning for Entities and Entity Details. Includes clean DRF APIs, idempotent ingestion services, and audit logging. Designed to be modular and extensible.

Getting started (Makefile)

1) Build and start containers
```bash
make build
make up
```

2) Load reference data and sample records (optional for demos)
```bash
make load-entity-types file='test_data/entity_types.json'
make batch-ingest file='test_data/sample_entities.json'
make batch-ingest file='test_data/sample_details.json'
```

3) Open API docs
```bash
http://localhost:8000/api/v1/schema/swagger-ui/
```

Linting

- Run both linters (after a `make build` to install tools):
```bash
make lint
```

- Run flake8 only (PEP8/quality):
```bash
make lint-flake8
```

- Run bandit only (security checks):
```bash
make lint-bandit
```

Project docs map

- ARCHITECTURE_OVERVIEW.md: Core architecture and SCD2 data model overview.
- API_REQUESTS.md: Ready-to-run cURL commands to exercise the API.
- MANAGEMENT_COMMANDS.md: How to use `load_entity_types`, `batch_ingest`, and `snapshot_refresh` (with `--dry-run`).
- TESTS_README.md: How to run the test suite (all/services/api/models) via Makefile.
- Advanced_Cockpit_CRM_SCD2_Assignment.md: Original assignment and scope details.
- PERFORMANCE.md: Indexing strategy and EXPLAIN/analysis for key queries.
- PII_GUIDELINES.md: Data classification and handling guidance.

Notes

- Auth: POST/PATCH endpoints require JWT (see API_REQUESTS.md for token obtain flow). GET endpoints are public (read-only).
- Data: Use Makefile commands above to seed data quickly for exploration.
