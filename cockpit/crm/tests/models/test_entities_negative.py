import pytest
from django.db import IntegrityError
from django.utils.timezone import now, timedelta

from crm.models import Entity, EntityType


@pytest.mark.django_db
def test_entity_unique_current_violation():
    et = EntityType.objects.get(code="PERSON")
    eid = "11111111-1111-1111-1111-111111111111"
    Entity.objects.create(
        entity_uuid=eid,
        type_code=et,
        display_name="A",
        valid_from=now(),
        valid_to=None,
        is_current=True,
        hashdiff="h1",
    )
    with pytest.raises(IntegrityError):
        Entity.objects.create(
            entity_uuid=eid,
            type_code=et,
            display_name="B",
            valid_from=now(),
            valid_to=None,
            is_current=True,
            hashdiff="h2",
    )


@pytest.mark.django_db
def test_entity_overlap_exclusion():
    et = EntityType.objects.get(code="PERSON")
    eid = "22222222-2222-2222-2222-222222222222"
    t0 = now()
    t1 = t0 + timedelta(minutes=10)
    t2 = t1 + timedelta(minutes=10)
    # first non-current window
    Entity.objects.create(
        entity_uuid=eid,
        type_code=et,
        display_name="A",
        valid_from=t0,
        valid_to=t2,
        is_current=False,
        hashdiff="ha",
    )
    # overlapping non-current window should violate exclusion
    with pytest.raises(IntegrityError):
        Entity.objects.create(
            entity_uuid=eid,
            type_code=et,
            display_name="B",
            valid_from=t1,
            valid_to=t2 + timedelta(minutes=5),
            is_current=False,
            hashdiff="hb",
        )


# Note: Additional SCD2 validity checks (current->valid_to NULL, valid_from<valid_to)
# are enforced at service level in this codebase, not as DB constraints for Entity.
