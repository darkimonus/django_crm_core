from typing import Any, Optional

from rest_framework import serializers

from crm.models.entities import EntityDetail, EntityType


# ----- Read-only serializers (responses) -----------------------------------
class EntityTypeSerializer(serializers.ModelSerializer):
    """
    Lightweight reference serializer for EntityType.
    """
    class Meta:
        model = EntityType
        fields = ("code", "title")


class EntityDetailSerializer(serializers.Serializer):
    """
    Current/as-of view for a single detail.
    We expose a unified 'value' derived from value_kind + value_* columns,
    while still returning the raw pieces for debugging.
    """
    entity_uuid = serializers.UUIDField()
    detail_code = serializers.CharField()
    value_kind = serializers.ChoiceField(choices=[c[0] for c in EntityDetail.Kind.choices])
    value = serializers.SerializerMethodField()

    # raw columns (optional but handy for debugging / admin)
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
        """Return the unified value depending on value_kind."""
        kind = getattr(obj, "value_kind", None)
        match kind:
            case "TEXT":
                return getattr(obj, "value_text", None)
            case "NUM":
                # To avoid Decimal JSON issues, return string form.
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
    """
    Current view for an Entity. We expect the view to attach a list of details
    into 'obj._current_details' (or 'obj._asof_details' for as-of endpoint).
    """
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
        if details is None:
            return []
        return EntityDetailSerializer(details, many=True).data


# ----- Write serializers (requests) ----------------------------------------
class EntityUpsertSerializer(serializers.Serializer):
    """
    Payload for POST/PATCH entity.
    For PATCH: 'entity_uuid' comes from URL, 'type_code' and/or 'display_name'
    are optional; if omitted, the view will reuse current values.
    """
    entity_uuid = serializers.UUIDField(required=False)  # not required on PATCH (from URL)
    type_code = serializers.CharField(required=False)
    display_name = serializers.CharField(required=False)
    change_ts = serializers.DateTimeField()
    actor = serializers.EmailField(required=False, allow_blank=True)
    correlation_id = serializers.CharField(required=False, allow_blank=True)

    # Optional inline detail changes (applied with the same change_ts by default)
    details = serializers.ListField(
        child=serializers.DictField(), required=False, allow_empty=True
    )

    def validate(self, attrs):
        # For POST we require entity_uuid, type_code and display_name.
        method = self.context.get("method")
        if method == "POST":
            for fld in ("entity_uuid", "type_code", "display_name"):
                if fld not in attrs:
                    raise serializers.ValidationError({fld: "This field is required for POST."})
        return attrs


class DetailUpsertSerializer(serializers.Serializer):
    """
    Payload for creating/updating a detail.
    'change_ts' is optional here; if omitted, caller should inject entity-level change_ts.
    """
    detail_code = serializers.CharField()
    value_kind = serializers.ChoiceField(choices=[c[0] for c in EntityDetail.Kind.choices])
    value = serializers.JSONField(required=False, allow_null=True)
    change_ts = serializers.DateTimeField(required=False)
    actor = serializers.EmailField(required=False, allow_blank=True)
    correlation_id = serializers.CharField(required=False, allow_blank=True)


class DetailUpsertInSerializer(serializers.Serializer):
    """One detail change item."""
    detail_code = serializers.CharField(
        help_text="Business code of the detail (e.g. EMAIL, PHONE, LEI)."
    )
    value_kind = serializers.ChoiceField(
        choices=[c[0] for c in EntityDetail.Kind.choices],
        help_text=(
            "Type of value. TEXT -> 'value' must be string; "
            "NUM -> number/decimal; TS -> RFC3339 timestamp; "
            "BOOL -> true/false; JSON -> object/array."
        ),
    )
    value = serializers.JSONField(
        required=False, allow_null=True,
        help_text="Detail value (type depends on value_kind)."
    )
    change_ts = serializers.DateTimeField(
        required=False,
        help_text="Optional override of entity-level change_ts for this detail."
    )
    actor = serializers.EmailField(required=False, allow_blank=True, help_text="Who performed the change.")
    correlation_id = serializers.CharField(required=False, allow_blank=True, help_text="Batch/job correlation id.")


class EntityCreateInSerializer(serializers.Serializer):
    """POST /entities payload."""
    entity_uuid = serializers.UUIDField(help_text="Stable business UUID for this entity (all versions share it).")
    type_code = serializers.CharField(help_text="Entity type (e.g. PERSON, INSTITUTION).")
    display_name = serializers.CharField(help_text="Human-friendly name for the entity.")
    change_ts = serializers.DateTimeField(help_text="RFC3339 timestamp when the change became effective.")
    actor = serializers.EmailField(required=False, allow_blank=True, help_text="Who performed the change.")
    correlation_id = serializers.CharField(required=False, allow_blank=True, help_text="Batch/job correlation id.")
    details = serializers.ListField(
        child=DetailUpsertInSerializer(),
        required=False, allow_empty=True,
        help_text="Optional list of detail upserts to apply with the same change_ts (unless overridden).",
    )


class EntityPatchInSerializer(serializers.Serializer):
    """PATCH /entities/{uuid} payload (partial SCD2 update)."""
    type_code = serializers.CharField(required=False, help_text="New type code. Omit to keep current.")
    display_name = serializers.CharField(required=False, help_text="New display name. Omit to keep current.")
    change_ts = serializers.DateTimeField(help_text="RFC3339 timestamp (> current.valid_from).")
    actor = serializers.EmailField(required=False, allow_blank=True, help_text="Who performed the change.")
    correlation_id = serializers.CharField(required=False, allow_blank=True, help_text="Batch/job correlation id.")
    details = serializers.ListField(
        child=DetailUpsertInSerializer(),
        required=False, allow_empty=True,
        help_text="Optional list of detail upserts to apply with the same change_ts (unless overridden).",
    )