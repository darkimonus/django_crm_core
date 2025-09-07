from decimal import Decimal, InvalidOperation

from rest_framework import serializers
from django.utils.dateparse import parse_datetime

from crm.models.entities import EntityDetail
from utils import parse_change_ts


class DetailUpsertSerializer(serializers.Serializer):
    detail_code = serializers.CharField()
    value_kind = serializers.ChoiceField(choices=[c[0] for c in EntityDetail.Kind.choices])
    value = serializers.JSONField(required=False, allow_null=True)
    change_ts = serializers.DateTimeField(required=False)
    actor = serializers.EmailField(required=False, allow_blank=True)
    correlation_id = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        code = attrs.get("detail_code")
        if code is not None:
            attrs["detail_code"] = str(code).strip().upper()

        kind = (attrs.get("value_kind") or "").upper()
        value = attrs.get("value")

        match kind:
            case "NUM":
                if value is None:
                    raise serializers.ValidationError({"value": "value is required for NUM."})
                try:
                    Decimal(str(value))
                except (InvalidOperation, ValueError, TypeError):
                    raise serializers.ValidationError({"value": "value must be numeric for NUM."})
            case "TS":
                if value is None:
                    raise serializers.ValidationError({"value": "value is required for TS."})
                try:
                    parse_change_ts(value)
                except Exception:
                    raise serializers.ValidationError({"value": "invalid timestamp for TS (ISO8601)."})
            case "BOOL" | "TEXT":
                if value is None:
                    raise serializers.ValidationError({"value": "value is required for BOOL/TEXT."})
            case _:
                pass

        if attrs.get("change_ts") is not None and parse_datetime(str(attrs["change_ts"])) is None:
            raise serializers.ValidationError({"change_ts": "Invalid timestamp."})
        return attrs


class DetailUpsertInSerializer(serializers.Serializer):
    detail_code = serializers.CharField(help_text="Business detail code, e.g. EMAIL")
    value_kind = serializers.ChoiceField(choices=[c[0] for c in EntityDetail.Kind.choices])
    value = serializers.JSONField(required=False, allow_null=True)
    change_ts = serializers.DateTimeField(required=False)
    actor = serializers.EmailField(required=False, allow_blank=True)
    correlation_id = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        code = attrs.get("detail_code")
        if code is not None:
            attrs["detail_code"] = str(code).strip().upper()

        kind = (attrs.get("value_kind") or "").upper()
        value = attrs.get("value")

        match kind:
            case "NUM":
                if value is None:
                    raise serializers.ValidationError({"value": "value is required for NUM."})
                try:
                    Decimal(str(value))
                except (InvalidOperation, ValueError, TypeError):
                    raise serializers.ValidationError({"value": "value must be numeric for NUM."})
            case "TS":
                if value is None:
                    raise serializers.ValidationError({"value": "value is required for TS."})
                try:
                    parse_change_ts(value)
                except Exception:
                    raise serializers.ValidationError({"value": "invalid timestamp for TS (ISO8601)."})
            case "BOOL" | "TEXT":
                if value is None:
                    raise serializers.ValidationError({"value": "value is required for BOOL/TEXT."})
            case _:
                pass
        return attrs
