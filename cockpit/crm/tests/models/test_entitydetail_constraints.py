import pytest
from django.db import IntegrityError, transaction
from django.utils.timezone import now, timedelta

from crm.models import EntityDetail


@pytest.mark.django_db
def test_detail_unique_current_violation():
    eid = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    code = "EMAIL"
    EntityDetail.objects.create(
        entity_uuid=eid,
        detail_code=code,
        value_kind="TEXT",
        value_text="a@example.com",
        valid_from=now(),
        valid_to=None,
        is_current=True,
        hashdiff="h1",
    )
    with pytest.raises(IntegrityError):
        EntityDetail.objects.create(
            entity_uuid=eid,
            detail_code=code,
            value_kind="TEXT",
            value_text="b@example.com",
            valid_from=now(),
            valid_to=None,
            is_current=True,
            hashdiff="h2",
        )


@pytest.mark.django_db
def test_detail_overlap_exclusion():
    eid = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
    code = "PHONE"
    t0 = now()
    t1 = t0 + timedelta(minutes=5)
    t2 = t1 + timedelta(minutes=5)
    EntityDetail.objects.create(
        entity_uuid=eid,
        detail_code=code,
        value_kind="TEXT",
        value_text="+1",
        valid_from=t0,
        valid_to=t2,
        is_current=False,
        hashdiff="ha",
    )
    with pytest.raises(IntegrityError):
        EntityDetail.objects.create(
            entity_uuid=eid,
            detail_code=code,
            value_kind="TEXT",
            value_text="+2",
            valid_from=t1,
            valid_to=t2 + timedelta(minutes=1),
            is_current=False,
            hashdiff="hb",
        )


@pytest.mark.django_db
def test_detail_kind_checks():
    eid = "cccccccc-cccc-cccc-cccc-cccccccccccc"
    # TEXT requires value_text
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            EntityDetail.objects.create(
                entity_uuid=eid,
                detail_code="X",
                value_kind="TEXT",
                value_text=None,
                valid_from=now(),
                valid_to=None,
                is_current=True,
                hashdiff="ht",
            )
    # NUM requires value_num
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            EntityDetail.objects.create(
                entity_uuid=eid,
                detail_code="Y",
                value_kind="NUM",
                value_num=None,
                valid_from=now(),
                valid_to=None,
                is_current=True,
                hashdiff="hn",
            )
    # TS requires value_ts
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            EntityDetail.objects.create(
                entity_uuid=eid,
                detail_code="Z",
                value_kind="TS",
                value_ts=None,
                valid_from=now(),
                valid_to=None,
                is_current=True,
                hashdiff="hs",
            )
    # BOOL requires value_bool
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            EntityDetail.objects.create(
                entity_uuid=eid,
                detail_code="B",
                value_kind="BOOL",
                value_bool=None,
                valid_from=now(),
                valid_to=None,
                is_current=True,
                hashdiff="hb",
            )
    # JSON requires value_json
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            EntityDetail.objects.create(
                entity_uuid=eid,
                detail_code="J",
                value_kind="JSON",
                value_json=None,
                valid_from=now(),
                valid_to=None,
                is_current=True,
                hashdiff="hj",
            )
