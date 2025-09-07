import pytest
from django.db import IntegrityError, transaction
from django.utils.timezone import now

from crm.models import Entity, EntityType


@pytest.mark.django_db
def test_entity_current_must_have_valid_to_null():
    et = EntityType.objects.get(code="PERSON")
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Entity.objects.create(
                entity_uuid="55555555-5555-5555-5555-555555555555",
                type_code=et,
                display_name="A",
                valid_from=now(),
                valid_to=now(),
                is_current=True,
                hashdiff="x",
            )


@pytest.mark.django_db
def test_entity_valid_bounds_if_not_null():
    et = EntityType.objects.get(code="PERSON")
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            t = now()
            Entity.objects.create(
                entity_uuid="66666666-6666-6666-6666-666666666666",
                type_code=et,
                display_name="A",
                valid_from=t,
                valid_to=t,  # must be strictly greater than valid_from
                is_current=False,
                hashdiff="y",
            )
