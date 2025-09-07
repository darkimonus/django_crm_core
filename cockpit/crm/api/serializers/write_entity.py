from rest_framework import serializers
from .write_detail import DetailUpsertInSerializer


class EntityCreateInSerializer(serializers.Serializer):
    entity_uuid = serializers.UUIDField(help_text="Stable business UUID")
    type_code = serializers.CharField(help_text="Entity type code, e.g. PERSON")
    display_name = serializers.CharField(help_text="Human-friendly name")
    change_ts = serializers.DateTimeField(help_text="Effective timestamp (ISO8601)")
    actor = serializers.EmailField(required=False, allow_blank=True)
    correlation_id = serializers.CharField(required=False, allow_blank=True)
    details = serializers.ListField(child=DetailUpsertInSerializer(), required=False, allow_empty=True)


class EntityPatchInSerializer(serializers.Serializer):
    type_code = serializers.CharField(required=False)
    display_name = serializers.CharField(required=False)
    change_ts = serializers.DateTimeField()
    actor = serializers.EmailField(required=False, allow_blank=True)
    correlation_id = serializers.CharField(required=False, allow_blank=True)
    details = serializers.ListField(child=DetailUpsertInSerializer(), required=False, allow_empty=True)
