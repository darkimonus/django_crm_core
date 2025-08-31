import pytest
from django.db.utils import IntegrityError
from crm.services.ingest import ingest_entity
from crm.models.entities import Entity


@pytest.mark.django_db
class TestNegativeConstraints:
    def test_constraint_violation(self):
        data = {
            'entity_uuid': '550e8400-e29b-41d4-a716-446655440040',
            'type_code': 'PERSON',
            'display_name': 'Grace',
            'change_ts': '2025-01-15T10:30:00Z',
            'actor': 'negative@example.com',
            'correlation_id': 'negative_batch'
        }
        ingest_entity(data)
        # Attempt to ingest duplicate entity_uuid should raise ConstraintViolation
        with pytest.raises(IntegrityError):
            ingest_entity(data)
