API Requests (cURL)

Prerequisites

- Start services: `make up` (or `make build` then `make up`).
- Seed reference types and sample data (optional but recommended for demo):
  - `make load-entity-types file='test_data/entity_types.json'`
  - `make batch-ingest file='test_data/sample_entities.json'`
  - `make batch-ingest file='test_data/sample_details.json'`

Auth (JWT)

- POST `/api/auth/token/` expects a Django user. Create one via `make manage createsuperuser` (interactive) or your preferred method.
- Example obtain token (replace credentials):
```bash
curl -s -X POST http://localhost:8000/api/auth/token/ \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"your_password"}'
```
- Use `Authorization: Bearer <access>` for POST/PATCH below.

List current entities

```bash
curl -s 'http://localhost:8000/api/v1/entities/?include_details=1' | jq .
```

Filter by type and detail (presence/value)

```bash
curl -s 'http://localhost:8000/api/v1/entities/?type=PERSON&detail_code=EMAIL' | jq .
```

```bash
curl -s 'http://localhost:8000/api/v1/entities/?detail_code=PHONE&detail_value=%2B123&detail_value_kind=TEXT' | jq .
```

Retrieve single entity (replace UUID)

```bash
curl -s 'http://localhost:8000/api/v1/entities/550e8400-e29b-41d4-a716-446655440001/' | jq .
```

Create entity (requires JWT)

```bash
curl -s -X POST http://localhost:8000/api/v1/entities/ \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "entity_uuid": "11111111-1111-1111-1111-111111111111",
    "type_code": "PERSON",
    "display_name": "Alice",
    "change_ts": "2025-08-28T10:00:00Z",
    "details": [{"detail_code": "EMAIL", "value_kind": "TEXT", "value": "alice@example.com"}]
  }' | jq .
```

Patch entity (requires JWT)

```bash
curl -s -X PATCH http://localhost:8000/api/v1/entities/11111111-1111-1111-1111-111111111111/ \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "display_name": "Alice S.",
    "change_ts": "2025-08-29T09:30:00Z",
    "details": [{"detail_code":"PHONE","value_kind":"TEXT","value":"+380501112233"}]
  }' | jq .
```

As-of snapshot

```bash
curl -s 'http://localhost:8000/api/v1/entities-asof/?as_of=2025-01-15T10:30:00Z&include_details=1' | jq .
```

Diff (audit) by date range

```bash
curl -s 'http://localhost:8000/api/v1/diff/?from=2025-01-01&to=2025-12-31' | jq .
```

