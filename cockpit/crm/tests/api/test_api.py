import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from crm.models.entities import Entity


@pytest.mark.django_db
class TestEntityAPI:
    def setup_method(self):
        self.client = APIClient()

    def test_create_entity(self):
        url = reverse('entity-list')
        data = {
            'entity_uuid': '550e8400-e29b-41d4-a716-446655440020',
            'type_code': 'PERSON',
            'display_name': 'Charlie',
            'change_ts': '2025-01-15T10:30:00Z',
            'actor': 'api@example.com',
            'correlation_id': 'api_batch'
        }
        response = self.client.post(url, data, format='json')
        assert response.status_code == 201

    def test_update_entity(self):
        entity = Entity.objects.create(
            entity_uuid='550e8400-e29b-41d4-a716-446655440021',
            type_code='PERSON',
            display_name='Dave',
            change_ts='2025-01-15T10:30:00Z',
            actor='initial@example.com',
            correlation_id='initial_batch'
        )
        url = reverse('entity-detail', args=[entity.pk])
        data = {
            'display_name': 'David',
            'change_ts': '2025-01-16T10:30:00Z',
            'actor': 'api_update@example.com',
            'correlation_id': 'update_batch'
        }
        response = self.client.patch(url, data, format='json')
        assert response.status_code == 200
        assert response.data['display_name'] == 'David'

    def test_list_entities(self):
        Entity.objects.create(
            entity_uuid='550e8400-e29b-41d4-a716-446655440022',
            type_code='PERSON',
            display_name='Eve',
            change_ts='2025-01-15T10:30:00Z',
            actor='list@example.com',
            correlation_id='list_batch'
        )
        url = reverse('entity-list')
        response = self.client.get(url)
        assert response.status_code == 200
        assert any(e['display_name'] == 'Eve' for e in response.data)

    def test_as_of(self):
        # Assuming an endpoint for as-of date filtering exists
        url = reverse('entity-list') + '?as_of=2025-01-15T10:30:00Z'
        response = self.client.get(url)
        assert response.status_code == 200

    def test_diff(self):
        # Assuming an endpoint for diff exists
        url = reverse('entity-diff')
        data = {
            'entity_uuid': '550e8400-e29b-41d4-a716-446655440020',
            'as_of_1': '2025-01-15T10:30:00Z',
            'as_of_2': '2025-01-16T10:30:00Z'
        }
        response = self.client.post(url, data, format='json')
        assert response.status_code == 200
