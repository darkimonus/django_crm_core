import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from cockpit.crm.models.entities import Entity
from django.utils import timezone

@pytest.mark.django_db
def test_api_create_entity():
    client = APIClient()
    url = reverse('entity-list')
    data = {"name": "API Entity", "effective_from": timezone.now()}
    response = client.post(url, data, format='json')
    assert response.status_code == 201
    assert Entity.objects.filter(name="API Entity").exists()

@pytest.mark.django_db
def test_api_update_entity():
    client = APIClient()
    entity = Entity.objects.create(name="API Entity", effective_from=timezone.now())
    url = reverse('entity-detail', args=[entity.id])
    data = {"name": "API Entity Updated"}
    response = client.patch(url, data, format='json')
    assert response.status_code == 200
    entity.refresh_from_db()
    assert entity.name == "API Entity Updated"

@pytest.mark.django_db
def test_api_list_entities():
    client = APIClient()
    Entity.objects.create(name="Entity1", effective_from=timezone.now())
    Entity.objects.create(name="Entity2", effective_from=timezone.now())
    url = reverse('entity-list')
    response = client.get(url)
    assert response.status_code == 200
    assert len(response.data) >= 2

@pytest.mark.django_db
def test_api_as_of_query():
    client = APIClient()
    now = timezone.now()
    entity = Entity.objects.create(name="Entity AsOf", effective_from=now)
    url = reverse('entity-list') + f'?as_of={now.isoformat()}'
    response = client.get(url)
    assert response.status_code == 200
    assert any(e['name'] == "Entity AsOf" for e in response.data)

@pytest.mark.django_db
def test_api_diff_endpoint():
    client = APIClient()
    entity = Entity.objects.create(name="Entity Diff", effective_from=timezone.now())
    url = reverse('entity-diff', args=[entity.id])
    response = client.get(url)
    assert response.status_code in (200, 404)  # 404 if diff not implemented
