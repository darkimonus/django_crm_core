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

# Test Commands
.PHONY: test
# Run all pytest tests in cockpit/crm (unit, API, idempotency, negative)
test:
	$(dc) exec cockpit-app-wsgi pytest crm -- --ds=cockpit.config.settings_test

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
	@echo ""
	@echo "Test Commands:"
	@echo "  make test-entities   - Test entity ingestion"
	@echo "  make test-details    - Test detail ingestion"
	@echo "  make test-combined   - Test combined data"
	@echo "  make test-large      - Test large dataset"
	@echo "  make test-errors     - Test error handling"
	@echo "  make test-updates    - Test SCD2 updates"
	@echo "  make test-snapshot   - Test snapshot refresh"
	@echo "  make test-py         - Run all pytest tests in cockpit/crm"
	@echo "  make test            - Run pytest"
	@echo "  make test-crm        - Run pytest for CRM tests"
	@echo ""
	@echo "Examples:"
	@echo "  make manage batch_ingest test_data/large_dataset.jsonl -- --batch-size 5 --dry-run"
	@echo "  make manage batch_ingest test_data/large_dataset.jsonl ARGS='--batch-size 5 --dry-run'"
	@echo "  make manage snapshot_refresh --dry-run"
	@echo "  make batch-ingest file='test_data/sample_entities.json'"
	@echo "  make batch-ingest file='test_data/large_dataset.jsonl' args='--batch-size 10'"
	@echo "  make snapshot-refresh args='--entity-types PERSON --since 2025-01-01T00:00:00Z'"
