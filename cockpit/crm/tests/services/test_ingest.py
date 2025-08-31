import pytest
from crm.services.ingest import ingest_entity
from crm.models.entities import Entity


@pytest.mark.django_db
class TestIngestIdempotency:
    def test_idempotent_ingest(self):
        data = {
            'entity_uuid': '550e8400-e29b-41d4-a716-446655440030',
            'type_code': 'PERSON',
            'display_name': 'Frank',
            'change_ts': '2025-01-15T10:30:00Z',
            'actor': 'ingest@example.com',
            'correlation_id': 'ingest_batch'
        }
        entity1 = ingest_entity(data)
        entity2 = ingest_entity(data)
        assert entity1.instance.pk == entity2.instance.pk
        assert entity1.instance.display_name == entity2.instance.display_name
