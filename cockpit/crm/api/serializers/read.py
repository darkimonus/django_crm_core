from typing import Any, Optional

from rest_framework import serializers

from crm.models.entities import EntityDetail, EntityType


class EntityTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntityType
        fields = ("code", "title")


class EntityDetailSerializer(serializers.Serializer):
    entity_uuid = serializers.UUIDField()
    detail_code = serializers.CharField()
    value_kind = serializers.ChoiceField(choices=[c[0] for c in EntityDetail.Kind.choices])
    value = serializers.SerializerMethodField()

    value_text = serializers.CharField(required=False, allow_null=True)
    value_num = serializers.CharField(required=False, allow_null=True)
    value_ts = serializers.DateTimeField(required=False, allow_null=True)
    value_bool = serializers.BooleanField(required=False, allow_null=True)
    value_json = serializers.JSONField(required=False, allow_null=True)

    valid_from = serializers.DateTimeField()
    valid_to = serializers.DateTimeField(allow_null=True)
    is_current = serializers.BooleanField()
    hashdiff = serializers.CharField()

    def get_value(self, obj) -> Optional[Any]:
        kind = getattr(obj, "value_kind", None)
        match kind:
            case "TEXT":
                return getattr(obj, "value_text", None)
            case "NUM":
                v = getattr(obj, "value_num", None)
                return None if v is None else str(v)
            case "TS":
                return getattr(obj, "value_ts", None)
            case "BOOL":
                return getattr(obj, "value_bool", None)
            case "JSON":
                return getattr(obj, "value_json", None)
            case _:
                return None


class EntitySerializer(serializers.Serializer):
    entity_uuid = serializers.UUIDField()
    type_code = serializers.CharField(source="type_code_id")
    display_name = serializers.CharField()
    valid_from = serializers.DateTimeField()
    valid_to = serializers.DateTimeField(allow_null=True)
    is_current = serializers.BooleanField()
    hashdiff = serializers.CharField()
    details = serializers.SerializerMethodField()

    def get_details(self, obj):
        details = getattr(obj, "_current_details", None) or getattr(obj, "_asof_details", None)
        return [] if details is None else EntityDetailSerializer(details, many=True).data


class HistoryResponseSerializer(serializers.Serializer):
    """Response schema for /entities/{uuid}/history endpoint."""
    entity = EntitySerializer(many=True)
    details = EntityDetailSerializer(many=True)


class AuditEventOutSerializer(serializers.Serializer):
    """Lightweight serializer for audit event responses in /diff."""
    happened_at = serializers.DateTimeField()
    actor = serializers.CharField()
    module = serializers.CharField()
    entity_uuid = serializers.UUIDField(allow_null=True)
    target_kind = serializers.CharField()
    target_key = serializers.JSONField()
    before = serializers.JSONField(allow_null=True)
    after = serializers.JSONField(allow_null=True)
    correlation_id = serializers.CharField(allow_null=True)


class DiffChangeItemSerializer(serializers.Serializer):
    happened_at = serializers.DateTimeField()
    actor = serializers.CharField()
    before = serializers.JSONField(allow_null=True)
    after = serializers.JSONField(allow_null=True)
    correlation_id = serializers.CharField(allow_null=True)


class DiffGroupOutSerializer(serializers.Serializer):
    entity_uuid = serializers.UUIDField()
    field = serializers.CharField()
    changes = DiffChangeItemSerializer(many=True)
