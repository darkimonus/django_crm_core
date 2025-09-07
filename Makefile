dc := docker compose -f docker-compose.yml --env-file docker-env

# Capture arguments for manage command
runargs :=
ifneq (,$(findstring $(firstword $(MAKECMDGOALS)),manage))
    runargs := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
    $(eval $(runargs): ; @true)
endif

.PHONY: build
build:
	$(dc) up -d --build;

.PHONY: up
up:
	$(dc) up -d;

.PHONY: stop
stop:
	$(dc) stop;

.PHONY: down
down:
	$(dc) down;

.PHONY: down-v
down-v:
	$(dc) down -v;

.PHONY: restart
restart:
	$(dc) stop && $(dc) up -d;

# Management Commands
.PHONY: manage
manage:
	$(dc) exec cockpit-app-wsgi python manage.py $(filter-out $@,$(MAKECMDGOALS)) $(ARGS)

.PHONY: batch-ingest
batch-ingest:
	$(dc) exec cockpit-app-wsgi python manage.py batch_ingest $(file) $(args);

.PHONY: batch-ingest-dry-run
batch-ingest-dry-run:
	$(dc) exec cockpit-app-wsgi python manage.py batch_ingest $(file) --dry-run $(args);

.PHONY: snapshot-refresh
snapshot-refresh:
	$(dc) exec cockpit-app-wsgi python manage.py snapshot_refresh $(args);

.PHONY: snapshot-refresh-dry-run
snapshot-refresh-dry-run:
	$(dc) exec cockpit-app-wsgi python manage.py snapshot_refresh --dry-run $(args);

# Entity types loader
.PHONY: load-entity-types
load-entity-types:
	$(dc) exec cockpit-app-wsgi python manage.py load_entity_types $(file) $(args);

# Test Data Commands
.PHONY: test-entities
test-entities:
	$(dc) exec cockpit-app-wsgi python manage.py batch_ingest test_data/sample_entities.json --dry-run;

.PHONY: test-details
test-details:
	$(dc) exec cockpit-app-wsgi python manage.py batch_ingest test_data/sample_details.json --dry-run;

.PHONY: test-combined
test-combined:
	$(dc) exec cockpit-app-wsgi python manage.py batch_ingest test_data/combined_data.json --dry-run;

.PHONY: test-large
test-large:
	$(dc) exec cockpit-app-wsgi python manage.py batch_ingest test_data/large_dataset.jsonl --batch-size 5 --dry-run;

.PHONY: test-errors
test-errors:
	$(dc) exec cockpit-app-wsgi python manage.py batch_ingest test_data/invalid_data.json --continue-on-error;

.PHONY: test-updates
test-updates:
	$(dc) exec cockpit-app-wsgi python manage.py batch_ingest test_data/update_scenarios.json --dry-run;

.PHONY: test-snapshot
test-snapshot:
	$(dc) exec cockpit-app-wsgi python manage.py snapshot_refresh --dry-run;

.PHONY: logs
logs:
	$(dc) logs -f cockpit-app-wsgi;

# Linting
.PHONY: lint lint-flake8 lint-bandit
lint: lint-flake8 lint-bandit

lint-flake8:
	$(dc) exec cockpit-app-wsgi sh -lc "flake8 ."

lint-bandit:
	$(dc) exec cockpit-app-wsgi sh -lc "bandit -c bandit.yaml -r ."
# Test Commands
.PHONY: test test-all test-services test-api test-models
# Run all pytest tests in cockpit/crm (unit, API, idempotency, negative)
test test-all:
	$(dc) exec cockpit-app-wsgi pytest crm --ds=config.settings_test -q

# Run only service-layer tests
test-services:
	$(dc) exec cockpit-app-wsgi pytest crm/tests/services --ds=config.settings_test -q

# Run only API tests
test-api:
	$(dc) exec cockpit-app-wsgi pytest crm/tests/api --ds=config.settings_test -q

# Run only model constraint/negative tests
test-models:
	$(dc) exec cockpit-app-wsgi pytest crm/tests/models --ds=config.settings_test -q

# Help command
.PHONY: help
help:
	@echo "Available commands:"
	@echo ""
	@echo "Docker Management:"
	@echo "  make up              - Start containers"
	@echo "  make down            - Stop containers"
	@echo "  make restart         - Restart containers"
	@echo "  make build           - Build and start containers"
	@echo "  make logs            - Show logs from the wsgi container"
	@echo ""
	@echo "Management Commands:"
	@echo "  make manage <command> [args ...] [-- <extra-args>] - Run any Django management command (use -- to pass options)"
	@echo "  make batch-ingest file='data.json'        - Run batch ingest"
	@echo "  make batch-ingest-dry-run file='data.json' - Run batch ingest (dry run)"
	@echo "  make snapshot-refresh                     - Run snapshot refresh"
	@echo "  make snapshot-refresh-dry-run             - Run snapshot refresh (dry run)"
	@echo "  make load-entity-types file='entity_types.json' - Load/update reference entity types"
	@echo ""
	@echo "Test Commands:"
	@echo "  make test            - Run all tests (alias: test-all)"
	@echo "  make test-all        - Run all tests in crm"
	@echo "  make test-services   - Run service-layer tests"
	@echo "  make test-api        - Run API tests"
	@echo "  make test-models     - Run model constraint tests"
	@echo ""
	@echo "Examples:"
	@echo "  make manage batch_ingest test_data/large_dataset.jsonl -- --batch-size 5 --dry-run"
	@echo "  make manage batch_ingest test_data/large_dataset.jsonl ARGS='--batch-size 5 --dry-run'"
	@echo "  make manage snapshot_refresh --dry-run"
	@echo "  make batch-ingest file='test_data/sample_entities.json'"
	@echo "  make batch-ingest file='test_data/large_dataset.jsonl' args='--batch-size 10'"
	@echo "  make snapshot-refresh args='--entity-types PERSON --since 2025-01-01T00:00:00Z'"
	@echo ""
	@echo "Linting:"
	@echo "  make lint            - Run flake8 and bandit"
	@echo "  make lint-flake8     - Run flake8 (PEP8/quality)"
	@echo "  make lint-bandit     - Run bandit (security checks)"
