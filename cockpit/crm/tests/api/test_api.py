import pytest
from uuid import UUID
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from crm.models import EntityType


@pytest.fixture(autouse=True)
def ensure_types(db):
    EntityType.objects.get_or_create(code="PERSON", defaults={"title": "Person"})


@pytest.mark.django_db
class TestEntityAPI:
    def setup_method(self):
        self.client = APIClient()
        # authenticate
        User = get_user_model()
        self.user = User.objects.create_user(username="tester", password="x")
        self.client.force_authenticate(user=self.user)

    def test_create_and_retrieve_with_details(self):
        url = reverse("crm:entities-list")
        data = {
            "entity_uuid": "11111111-1111-1111-1111-111111111111",
            "type_code": "PERSON",
            "display_name": "Charlie",
            "change_ts": "2025-01-15T10:30:00Z",
            "details": [{"detail_code": "EMAIL", "value_kind": "TEXT", "value": "c@example.com"}],
        }
        resp = self.client.post(url, data, format="json")
        assert resp.status_code == 201
        eid = data["entity_uuid"]
        r2 = self.client.get(reverse("crm:entities-detail", kwargs={"uuid": eid}))
        assert r2.status_code == 200
        assert any(d["detail_code"] == "EMAIL" for d in r2.data.get("details", []))

    def test_patch_and_filters(self):
        eid = "22222222-2222-2222-2222-222222222222"
        self.client.post(reverse("crm:entities-list"), {
            "entity_uuid": eid, "type_code": "PERSON", "display_name": "Dave", "change_ts": "2025-01-15T10:30:00Z"
        }, format="json")
        r = self.client.patch(reverse("crm:entities-detail", kwargs={"uuid": eid}), {
            "display_name": "David", "change_ts": "2025-01-16T10:30:00Z",
            "details": [{"detail_code": "PHONE", "value_kind": "TEXT", "value": "+123"}],
        }, format="json")
        assert r.status_code == 200
        # list with include_details
        rlist = self.client.get(reverse("crm:entities-list") + "?include_details=1")
        assert rlist.status_code == 200
        # filter by detail
        rfilter = self.client.get(reverse("crm:entities-list") + "?detail_code=PHONE&detail_value=%2B123&detail_value_kind=TEXT")
        assert rfilter.status_code == 200
        assert any(e["entity_uuid"] == eid for e in rfilter.data)

    def test_asof_and_diff(self):
        r = self.client.get(reverse("crm:entities-asof") + "?as_of=2025-01-15T10:30:00Z")
        assert r.status_code in (200, 400)  # 400 if no as_of provided earlier
        r2 = self.client.get(reverse("crm:entities-diff") + "?from=2025-01-01&to=2025-12-31")
        assert r2.status_code == 200


@pytest.mark.django_db
class TestAuthAPI:
    def test_unauthenticated_writes_blocked(self):
        client = APIClient()  # no auth
        url = reverse("crm:entities-list")
        data = {
            "entity_uuid": "33333333-3333-3333-3333-333333333333",
            "type_code": "PERSON",
            "display_name": "Unauth",
            "change_ts": "2025-01-15T10:30:00Z",
        }
        resp = client.post(url, data, format="json")
        assert resp.status_code in (401, 403)


@pytest.mark.django_db
class TestFiltersAPI:
    def setup_method(self):
        self.client = APIClient()
        User = get_user_model()
        self.user = User.objects.create_user(username="fuser", password="x")
        self.client.force_authenticate(user=self.user)

    def _create(self, uuid: str, name: str):
        return self.client.post(reverse("crm:entities-list"), {
            "entity_uuid": uuid, "type_code": "PERSON", "display_name": name,
            "change_ts": "2025-01-15T10:30:00Z",
        }, format="json")

    def test_search_and_type_filter(self):
        self._create("44444444-4444-4444-4444-444444444441", "Alpha Bravo")
        self._create("44444444-4444-4444-4444-444444444442", "Charlie Delta")
        # search by fragment
        r = self.client.get(reverse("crm:entities-list") + "?search=char")
        assert r.status_code == 200
        assert any("Charlie" in e["display_name"] for e in r.data)
        # type filter (single available type)
        r2 = self.client.get(reverse("crm:entities-list") + "?type=PERSON")
        assert r2.status_code == 200
        assert len(r2.data) >= 2

    def test_detail_presence_and_bool_value(self):
        eid = "55555555-5555-5555-5555-555555555555"
        self._create(eid, "Echo Foxtrot")
        # add a boolean detail and a phone
        self.client.patch(reverse("crm:entities-detail", kwargs={"uuid": eid}), {
            "change_ts": "2025-01-16T00:00:00Z",
            "details": [
                {"detail_code": "PHONE", "value_kind": "TEXT", "value": "+1800555"},
                {"detail_code": "SUBSCRIBED", "value_kind": "BOOL", "value": True},
            ],
        }, format="json")
        # presence-only
        rp = self.client.get(reverse("crm:entities-list") + "?detail_code=PHONE")
        assert any(e["entity_uuid"] == eid for e in rp.data)
        # typed bool filter
        rb = self.client.get(reverse("crm:entities-list") + "?detail_code=SUBSCRIBED&detail_value=true&detail_value_kind=BOOL")
        assert any(e["entity_uuid"] == eid for e in rb.data)


@pytest.mark.django_db
class TestAsOfAPI:
    def setup_method(self):
        self.client = APIClient()
        User = get_user_model()
        self.user = User.objects.create_user(username="auser", password="x")
        self.client.force_authenticate(user=self.user)

    def test_missing_asof_param_400(self):
        r = self.client.get(reverse("crm:entities-asof"))
        assert r.status_code == 400

    def test_asof_with_details_truthy_parse(self):
        eid = "66666666-6666-6666-6666-666666666666"
        # create and add a detail starting at 10:00
        self.client.post(reverse("crm:entities-list"), {
            "entity_uuid": eid, "type_code": "PERSON", "display_name": "Golf Hotel",
            "change_ts": "2025-01-15T09:00:00Z",
        }, format="json")
        self.client.patch(reverse("crm:entities-detail", kwargs={"uuid": eid}), {
            "change_ts": "2025-01-15T10:00:00Z",
            "details": [{"detail_code": "EMAIL", "value_kind": "TEXT", "value": "gh@example.com"}],
        }, format="json")
        # query at 10:30 with include_details=yes
        r = self.client.get(reverse("crm:entities-asof") + "?as_of=2025-01-15T10:30:00Z&include_details=yes")
        assert r.status_code == 200
        assert any(any(d.get("detail_code") == "EMAIL" for d in e.get("details", [])) for e in r.data)


@pytest.mark.django_db
class TestDiffAPI:
    def setup_method(self):
        self.client = APIClient()
        User = get_user_model()
        self.user = User.objects.create_user(username="duser", password="x")
        self.client.force_authenticate(user=self.user)

    def test_diff_groups_entity_and_detail_changes(self):
        eid = "77777777-7777-7777-7777-777777777777"
        # create entity and then update name + add detail
        self.client.post(reverse("crm:entities-list"), {
            "entity_uuid": eid, "type_code": "PERSON", "display_name": "Ivan",
            "change_ts": "2025-01-01T09:00:00Z",
        }, format="json")
        self.client.patch(reverse("crm:entities-detail", kwargs={"uuid": eid}), {
            "display_name": "Ivan Petrov",
            "change_ts": "2025-01-01T10:00:00Z",
            "details": [{"detail_code": "EMAIL", "value_kind": "TEXT", "value": "ivan@example.com"}],
        }, format="json")
        r = self.client.get(reverse("crm:entities-diff") + "?from=2025-01-01&to=2025-12-31")
        assert r.status_code == 200
        # flatten groups by field
        fields = {g["field"] for g in r.data if UUID(g["entity_uuid"]) == UUID(eid)}
        assert "display_name" in fields or "EMAIL" in fields
        # ensure unified values are present in changes
        any_changes = any(len(g.get("changes", [])) > 0 for g in r.data)
        assert any_changes


@pytest.mark.django_db
class TestIdempotencyAPI:
    def setup_method(self):
        self.client = APIClient()
        User = get_user_model()
        self.user = User.objects.create_user(username="iuser", password="x")
        self.client.force_authenticate(user=self.user)

    def test_patch_idempotency_same_payload(self):
        from crm.models import Entity, EntityDetail
        eid = "88888888-8888-8888-8888-888888888888"
        # create
        r1 = self.client.post(reverse("crm:entities-list"), {
            "entity_uuid": eid, "type_code": "PERSON", "display_name": "Jane",
            "change_ts": "2025-01-01T09:00:00Z",
        }, format="json")
        assert r1.status_code == 201
        # first patch (update name + add detail)
        payload = {
            "display_name": "Jane Roe",
            "change_ts": "2025-01-01T10:00:00Z",
            "details": [{"detail_code": "EMAIL", "value_kind": "TEXT", "value": "jane@example.com"}],
        }
        r2 = self.client.patch(reverse("crm:entities-detail", kwargs={"uuid": eid}), payload, format="json")
        assert r2.status_code == 200
        # replay same patch -> should be noop at service layer
        r3 = self.client.patch(reverse("crm:entities-detail", kwargs={"uuid": eid}), payload, format="json")
        assert r3.status_code == 200
        # verify version counts unchanged by replay
        assert Entity.objects.filter(entity_uuid=eid).count() == 2  # created + updated
        assert EntityDetail.objects.filter(entity_uuid=eid, detail_code="EMAIL").count() == 1  # only initial detail
