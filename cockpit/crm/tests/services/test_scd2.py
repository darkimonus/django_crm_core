import pytest
from datetime import timedelta
from django.utils.timezone import now

from crm.models import EntityType, Entity
from crm.services.scd2 import upsert_entity
from crm.services.exceptions import BackdatedIntervalError, TypeCodeNotFound


@pytest.fixture(autouse=True)
def ensure_types(db):
    EntityType.objects.get_or_create(code="PERSON", defaults={"title": "Person"})


@pytest.mark.django_db
def test_entity_create_and_noop():
    ts = now()
    res1 = upsert_entity(
        entity_uuid="550e8400-e29b-41d4-a716-446655440010",
        type_code="PERSON",
        display_name="Alice",
        change_ts=ts,
        actor="test@example.com",
    )
    assert res1.status == "created"
    res2 = upsert_entity(
        entity_uuid="550e8400-e29b-41d4-a716-446655440010",
        type_code="PERSON",
        display_name="Alice",
        change_ts=ts,
        actor="test@example.com",
    )
    assert res2.status == "noop"


@pytest.mark.django_db
def test_entity_update_and_backdated_error():
    start = now()
    eid = "550e8400-e29b-41d4-a716-446655440011"
    upsert_entity(entity_uuid=eid, type_code="PERSON", display_name="Bob", change_ts=start)
    res = upsert_entity(entity_uuid=eid, type_code="PERSON", display_name="Bobby", change_ts=start + timedelta(minutes=1))
    assert res.status == "updated"
    with pytest.raises(BackdatedIntervalError):
        upsert_entity(entity_uuid=eid, type_code="PERSON", display_name="Bobby2", change_ts=start)


@pytest.mark.django_db
def test_invalid_type_code():
    with pytest.raises(TypeCodeNotFound):
        upsert_entity(entity_uuid="550e8400-e29b-41d4-a716-446655440099", type_code="UNKNOWN", display_name="X", change_ts=now())
