import pytest
from crm.models import EntityType
from crm.services.ingest import ingest_entity, ingest_detail


@pytest.fixture(autouse=True)
def ensure_types(db):
    EntityType.objects.get_or_create(code="PERSON", defaults={"title": "Person"})


@pytest.mark.django_db
def test_ingest_entity_idempotent():
    payload = {
        "entity_uuid": "550e8400-e29b-41d4-a716-446655440030",
        "type_code": "PERSON",
        "display_name": "Frank",
        "change_ts": "2025-01-15T10:30:00Z",
    }
    r1 = ingest_entity(payload)
    r2 = ingest_entity(payload)
    assert r1.status == "created"
    assert r2.status == "noop"


@pytest.mark.django_db
def test_ingest_detail_create_and_noop():
    ingest_entity({
        "entity_uuid": "550e8400-e29b-41d4-a716-446655440031",
        "type_code": "PERSON",
        "display_name": "Greg",
        "change_ts": "2025-01-15T10:30:00Z",
    })
    d1 = ingest_detail({
        "entity_uuid": "550e8400-e29b-41d4-a716-446655440031",
        "detail_code": "EMAIL",
        "value_kind": "TEXT",
        "value": "greg@example.com",
        "change_ts": "2025-01-15T10:30:00Z",
    })
    d2 = ingest_detail({
        "entity_uuid": "550e8400-e29b-41d4-a716-446655440031",
        "detail_code": "EMAIL",
        "value_kind": "TEXT",
        "value": "greg@example.com",
        "change_ts": "2025-01-15T10:30:00Z",
    })
    assert d1.status == "created"
    assert d2.status == "noop"
