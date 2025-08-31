from django.db.models import Q, Exists, OuterRef

from django_filters.rest_framework import FilterSet, filters

from crm.models.entities import Entity, EntityDetail


class EntitiesFilter(FilterSet):
    """
    Filtering:
      - type: exact match on Entity.type_code_id
      - detail_code + detail_value: filter entities by current detail value
    """
    type = filters.CharFilter(field_name="type_code_id", lookup_expr="exact")
    detail_code = filters.CharFilter(method="filter_by_detail")
    detail_value = filters.CharFilter(method="filter_by_detail")

    def filter_by_detail(self, qs, name, value):
        """
        Filter entities by a current detail (detail_code + detail_value).
        We support TEXT/BOOL/NUM via simple equality. For TS/JSON you can extend.
        """
        # read both values from query params
        code = self.data.get("detail_code")
        val = self.data.get("detail_value")
        if not code or val is None:
            return qs

        # We don't know the kind here; assume TEXT equality on value_text by default.
        subquery = EntityDetail.objects.filter(
            entity_uuid=OuterRef("entity_uuid"),
            is_current=True,
            detail_code=code,
        ).filter(
            Q(value_text__iexact=val) |
            Q(value_num__isnull=False, value_num=val) |
            Q(value_bool__isnull=False, value_bool__in=[val.lower() in {"1", "true", "t", "yes", "y"}])
        )
        return qs.filter(Exists(subquery))

    class Meta:
        model = Entity
        fields = ["type"]
