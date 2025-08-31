# Django Management Commands

This document describes the Django management commands available for batch ingest and snapshot refresh operations.

## Entity Type Loader Command

The `load_entity_types` command allows you to load or update entity types in the database from a JSON file.

### Usage

```bash
make manage load_entity_types test_data/entity_types.json
make manage load_entity_types test_data/entity_types.json -- --dry-run
```

### Arguments

- `file_path`: Path to JSON file containing entity types (array of objects with `code` and `title`)

### Options

- `--dry-run`: Show what would be loaded without making changes

### JSON Format Example

```json
[
  {"code": "PERSON", "title": "Person"},
  {"code": "COMPANY", "title": "Company"},
  {"code": "TRUST", "title": "Trust"},
  {"code": "FUND", "title": "Fund"}
]
```

### Example

```bash
make manage load_entity_types test_data/entity_types.json -- --dry-run
make manage load_entity_types test_data/entity_types.json
```

## Batch Ingest Command

The `batch_ingest` command allows you to bulk load entities and details from JSON or JSONL files.

### Usage

```bash
make manage batch_ingest test_data/sample_entities.json -- --dry-run
make manage batch_ingest test_data/sample_details.json -- --dry-run
make manage batch_ingest test_data/combined_data.json -- --dry-run
make manage batch_ingest test_data/large_dataset.jsonl -- --batch-size 5 --dry-run
make manage batch_ingest test_data/invalid_data.json -- --continue-on-error
make manage batch_ingest test_data/update_scenarios.json -- --dry-run
```

### Arguments

- `file_path`: Path to JSON or JSONL file containing ingest data

### Options

- `--actor`: Actor name for audit trail (default: `batch_ingest@management`)
- `--correlation-id`: Correlation ID for audit trail (defaults to filename)
- `--dry-run`: Process data without committing to database
- `--batch-size`: Number of records to process in each batch (default: 1000)
- `--continue-on-error`: Continue processing even if individual records fail

### File Formats

#### JSON Format
The JSON file should contain an array of records or a dictionary with a "records" key:

```json
[
  {
    "type": "entity",
    "entity_uuid": "550e8400-e29b-41d4-a716-446655440001",
    "type_code": "PERSON",
    "display_name": "John Doe",
    "change_ts": "2025-01-15T10:30:00Z",
    "actor": "etl@test.com",
    "correlation_id": "test_batch_001"
  },
  {
    "type": "detail",
    "entity_uuid": "550e8400-e29b-41d4-a716-446655440001",
    "detail_code": "EMAIL",
    "value_kind": "TEXT",
    "value": "john.doe@example.com",
    "change_ts": "2025-01-15T10:30:00Z",
    "actor": "etl@test.com",
    "correlation_id": "test_batch_001"
  }
]
```

#### JSONL Format
Each line should contain a single JSON object:

```jsonl
{"type": "entity", "entity_uuid": "770e8400-e29b-41d4-a716-446655440001", "type_code": "PERSON", "display_name": "User 001", "change_ts": "2025-01-17T08:00:00Z", "actor": "etl@test.com", "correlation_id": "large_batch_001"}
{"type": "detail", "entity_uuid": "770e8400-e29b-41d4-a716-446655440001", "detail_code": "EMAIL", "value_kind": "TEXT", "value": "user001@example.com", "change_ts": "2025-01-17T08:00:00Z", "actor": "etl@test.com", "correlation_id": "large_batch_001"}
```

### Record Types

#### Entity Records
Required fields:
- `type`: Must be "entity"
- `entity_uuid`: Unique identifier for the entity
- `type_code`: Entity type code (must exist in EntityType table)
- `display_name`: Human-readable name for the entity
- `change_ts`: Timestamp when the change occurred (ISO format)

Optional fields:
- `actor`: Actor performing the change (defaults to command actor)
- `correlation_id`: Correlation ID for tracking (defaults to command correlation_id)

#### Detail Records
Required fields:
- `type`: Must be "detail"
- `entity_uuid`: Entity UUID this detail belongs to
- `detail_code`: Detail type code
- `value_kind`: Data type ("TEXT", "NUM", "TS", "BOOL", "JSON")
- `change_ts`: Timestamp when the change occurred (ISO format)

Optional fields:
- `value`: The actual value (required for all types except when value is null)
- `actor`: Actor performing the change (defaults to command actor)
- `correlation_id`: Correlation ID for tracking (defaults to command correlation_id)

### Examples

#### Basic Entity Ingestion
```bash
make manage batch_ingest test_data/sample_entities.json -- --dry-run
```

#### Basic Detail Ingestion
```bash
make manage batch_ingest test_data/sample_details.json -- --dry-run
```

#### Combined Data Ingestion
```bash
make manage batch_ingest test_data/combined_data.json -- --dry-run
```

#### Large Dataset (Performance)
```bash
make manage batch_ingest test_data/large_dataset.jsonl -- --batch-size 5 --dry-run
```

#### Error Handling
```bash
make manage batch_ingest test_data/invalid_data.json -- --continue-on-error
```

#### SCD2 Update Scenarios
```bash
make manage batch_ingest test_data/update_scenarios.json -- --dry-run
```

## Snapshot Refresh Command

The `snapshot_refresh` command allows you to refresh snapshots and materialized views for CRM data.

### Usage

```bash
make manage snapshot_refresh -- --dry-run
make manage snapshot_refresh -- --entity-types PERSON --dry-run
make manage snapshot_refresh -- --since "2025-01-19T00:00:00Z" --dry-run
```

### Options

- `--entity-types`: Specific entity types to refresh (default: all)
- `--detail-codes`: Specific detail codes to refresh (default: all)
- `--since`: Only refresh data changed since this timestamp (ISO format)
- `--dry-run`: Show what would be refreshed without making changes
- `--force`: Force refresh even if no changes detected
- `--create-snapshot-table`: Create a new snapshot table with current timestamp

### Examples

#### Basic Refresh
```bash
make manage snapshot_refresh -- --dry-run
```

#### Refresh Specific Entity Types
```bash
make manage snapshot_refresh -- --entity-types PERSON --dry-run
```

#### Refresh Since Specific Time
```bash
make manage snapshot_refresh -- --since "2025-01-19T00:00:00Z" --dry-run
```

#### Force Refresh
```bash
make manage snapshot_refresh -- --force
```

#### Create Snapshot Table
```bash
make manage snapshot_refresh -- --create-snapshot-table
```

#### Combined Options
```bash
make manage snapshot_refresh -- --entity-types PERSON --since "2025-01-19T00:00:00Z" --dry-run
```

## Python Test Command

The Makefile provides a convenient command to run all Python (pytest) tests in the `cockpit/crm` directory, including unit, API, idempotency, and negative tests:

```bash
make test-py
```

This will execute all test files (e.g., `test_scd2.py`, `test_ingest.py`, `test_entities_negative.py`, `api/tests.py`) inside the container using pytest. Use this command to validate code changes and ensure all business logic and API endpoints are covered.

# Management Commands

## Testing

Run all tests with pytest:

```bash
make test
```

Run tests for crm app only:

```bash
make test-crm
```

## Error Handling

### Batch Ingest Errors

The batch ingest command handles various error scenarios:

1. **File not found**: Command will fail immediately
2. **Invalid JSON**: Command will fail with specific error message
3. **Missing required fields**: Individual record errors are logged
4. **Invalid entity type**: Record errors are logged
5. **Backdated intervals**: Record errors are logged

Use `--continue-on-error` to process remaining records even if some fail.

### Snapshot Refresh Errors

The snapshot refresh command handles:

1. **Invalid timestamp format**: Command will fail immediately
2. **No changes detected**: Command will exit gracefully (use `--force` to override)
3. **Database errors**: Command will fail with specific error message

## Performance Considerations

- Use appropriate batch sizes (default 1000) based on your data volume
- JSONL format is more memory-efficient for large files
- Consider using `--dry-run` first to validate data
- Monitor database performance during large imports

## Monitoring and Logging

Both commands provide detailed output including:

- Processing statistics
- Error counts and details
- Progress indicators for large operations
- Final summary with totals

Logs are written to Django's logging system and can be configured in settings.

## Using Makefile Commands (Recommended)

For convenience, you can use the Makefile commands which handle Docker container execution:

```bash
make manage batch_ingest test_data/sample_entities.json -- --dry-run
make manage batch_ingest test_data/sample_details.json -- --dry-run
make manage batch_ingest test_data/combined_data.json -- --dry-run
make manage batch_ingest test_data/large_dataset.jsonl -- --batch-size 5 --dry-run
make manage batch_ingest test_data/invalid_data.json -- --continue-on-error
make manage batch_ingest test_data/update_scenarios.json -- --dry-run
make manage snapshot_refresh -- --dry-run
```

## Integration with CI/CD

These commands can be integrated into CI/CD pipelines:

```bash
# Validate data before deployment
make manage batch_ingest test_data/sample_entities.json -- --dry-run

# Refresh snapshots after deployment
make manage snapshot_refresh -- --force
```

## Troubleshooting

### Common Issues

1. **Entity type not found**: Ensure entity types exist in the database (use `load_entity_types` command)
2. **Invalid timestamp format**: Use ISO format (e.g., "2025-01-15T10:30:00Z")
3. **Permission errors**: Ensure database user has appropriate permissions
4. **Memory issues**: Reduce batch size for large files

### Debug Mode

Enable Django debug mode for more detailed error messages:

```bash
DJANGO_DEBUG=1 make manage batch_ingest test_data/sample_entities.json -- --dry-run
```
