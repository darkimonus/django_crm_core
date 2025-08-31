import pytest
from django.utils.timezone import now, timedelta
from crm.models.entities import Entity
from crm.services.scd2 import upsert_entity


@pytest.mark.django_db
class TestSCD2Transitions:
    def test_create_entity(self):
        entity_data = {
            'entity_uuid': '550e8400-e29b-41d4-a716-446655440010',
            'type_code': 'PERSON',
            'display_name': 'Alice',
            'change_ts': now(),
            'actor': 'test@example.com',
            'correlation_id': 'test_batch'
        }
        result = upsert_entity(
            entity_uuid=entity_data['entity_uuid'],
            type_code=entity_data['type_code'],
            display_name=entity_data['display_name'],
            change_ts=entity_data['change_ts'],
            actor=entity_data['actor'],
            correlation_id=entity_data['correlation_id'],
        )
        assert result.instance.pk is not None
        assert result.instance.display_name == 'Alice'

    def test_update_entity(self):
        entity = Entity.objects.create(
            entity_uuid='550e8400-e29b-41d4-a716-446655440011',
            type_code='PERSON',
            display_name='Bob',
            valid_from=now() - timedelta(days=1),
            valid_to=None,
            is_current=True,
            hashdiff='',
            actor='initial@example.com',
            correlation_id='initial_batch'
        )
        update_data = {
            'entity_uuid': '550e8400-e29b-41d4-a716-446655440011',
            'type_code': 'PERSON',
            'display_name': 'Bobby',
            'change_ts': now(),
            'actor': 'update@example.com',
            'correlation_id': 'update_batch'
        }
        result = upsert_entity(
            entity_uuid=update_data['entity_uuid'],
            type_code=update_data['type_code'],
            display_name=update_data['display_name'],
            change_ts=update_data['change_ts'],
            actor=update_data['actor'],
            correlation_id=update_data['correlation_id'],
        )
        assert result.instance.display_name == 'Bobby'
        assert result.instance.change_ts > entity.valid_from
