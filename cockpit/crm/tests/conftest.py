import pytest

from crm.models import EntityType


@pytest.fixture(autouse=True)
def ensure_entity_types(db):
    EntityType.objects.get_or_create(code="PERSON", defaults={"title": "Person"})
    EntityType.objects.get_or_create(code="COMPANY", defaults={"title": "Company"})

