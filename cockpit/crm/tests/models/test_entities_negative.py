import pytest
from cockpit.crm.models.entities import Entity
from django.db import IntegrityError
from django.utils import timezone


@pytest.mark.django_db
def test_missing_required_field():
    with pytest.raises(IntegrityError):
        Entity.objects.create(effective_from=timezone.now())


@pytest.mark.django_db
def test_unique_constraint_violation():
    Entity.objects.create(name="Unique Entity", effective_from=timezone.now())
    with pytest.raises(IntegrityError):
        Entity.objects.create(name="Unique Entity", effective_from=timezone.now())


@pytest.mark.django_db
def test_invalid_foreign_key():
    with pytest.raises(Exception):
        Entity.objects.create(name="Bad FK", effective_from=timezone.now(), related_id=999999)


@pytest.mark.django_db
def test_invalid_data_type():
    with pytest.raises(Exception):
        Entity.objects.create(name=12345, effective_from=timezone.now())
