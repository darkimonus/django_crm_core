import pytest
from crm.services.ingest import ingest_entity
from crm.services.exceptions import TypeCodeNotFound


@pytest.mark.django_db
def test_type_code_not_found():
    with pytest.raises(TypeCodeNotFound):
        ingest_entity({
            "entity_uuid": "550e8400-e29b-41d4-a716-446655440040",
            "type_code": "NOPE",
            "display_name": "Grace",
            "change_ts": "2025-01-15T10:30:00Z",
        })
