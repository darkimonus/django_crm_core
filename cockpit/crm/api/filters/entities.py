import json
from decimal import Decimal

from django.db.models import Q, Exists, OuterRef
from django.utils.dateparse import parse_datetime
from django_filters.rest_framework import FilterSet, filters

from crm.models.entities import Entity, EntityDetail


class EntitiesFilter(FilterSet):
    type = filters.CharFilter(field_name="type_code_id", lookup_expr="exact")
    detail_code = filters.CharFilter(method="filter_by_detail")
    detail_value = filters.CharFilter(method="filter_by_detail")
    detail_value_kind = filters.CharFilter(method="filter_by_detail")

    def filter_by_detail(self, qs, name, value):
        code = (self.data.get("detail_code") or "").strip().upper()
        if not code:
            return qs

        val = self.data.get("detail_value")
        kind = (self.data.get("detail_value_kind") or "").strip().upper()

        sub = EntityDetail.objects.filter(
            entity_uuid=OuterRef("entity_uuid"), is_current=True, detail_code=code
        )

        if val is None or val == "":
            return qs.filter(Exists(sub))

        match kind:
            case "TEXT":
                sub = sub.filter(value_text__iexact=val)
            case "NUM":
                try:
                    num = Decimal(str(val))
                    sub = sub.filter(value_num=num)
                except Exception:
                    return qs.none()
            case "BOOL":
                truthy = str(val).lower() in {"1", "true", "t", "yes", "y"}
                sub = sub.filter(value_bool__in=[truthy])
            case "TS":
                ts = parse_datetime(str(val))
                if ts is None:
                    return qs.none()
                sub = sub.filter(value_ts=ts)
            case "JSON":
                try:
                    parsed = json.loads(val)
                except Exception:
                    return qs.none()
                sub = sub.filter(value_json__contains=parsed)
            case _:
                truthy = str(val).lower() in {"1", "true", "t", "yes", "y"}
                sub = sub.filter(
                    Q(value_text__iexact=val) |
                    Q(value_num__isnull=False, value_num=val) |
                    Q(value_bool__isnull=False, value_bool__in=[truthy])
                )
        return qs.filter(Exists(sub))

    class Meta:
        model = Entity
        fields = ["type"]
