import uuid

from django.db import models
from django.db.models import Q, F, CheckConstraint
from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import RangeOperators

from .mixins import SCD2Mixin


class EntityType(models.Model):
    code = models.CharField(max_length=50, primary_key=True)
    title = models.CharField(max_length=200)

    class Meta:
        db_table = "entity_type"

    def __str__(self):
        return f"{self.code}"


class EntityDetail(SCD2Mixin):
    """
    Typed details for entity.
    """
    entity_uuid = models.UUIDField(db_index=True)
    detail_code = models.CharField(max_length=50)

    class Kind(models.TextChoices):
        TEXT = "TEXT", "Text"
        NUM = "NUM", "Numeric"
        TS = "TS", "Timestamp"
        BOOL = "BOOL", "Boolean"
        JSON = "JSON", "JSON"

    value_kind = models.CharField(max_length=8, choices=Kind.choices)
    value_text = models.TextField(null=True, blank=True)  # NOSONAR
    value_num = models.DecimalField(max_digits=30, decimal_places=10, null=True, blank=True)
    value_ts = models.DateTimeField(null=True, blank=True)
    value_bool = models.BooleanField(null=True, blank=True)
    value_json = models.JSONField(null=True, blank=True)

    hashdiff = models.CharField(max_length=64, db_index=True)

    class Meta:
        db_table = "entity_detail"
        constraints = [
            models.UniqueConstraint(
                fields=["entity_uuid", "detail_code"],
                condition=Q(is_current=True),
                name="uniq_edetail_current",
            ),

            ExclusionConstraint(
                name="edetail_no_overlap",
                index_type="GIST",
                expressions=[
                    (F("entity_uuid"), "="),
                    (F("detail_code"), "="),
                    (
                        models.Func(F("valid_from"), F("valid_to"), function="tstzrange"),
                        RangeOperators.OVERLAPS,
                    ),
                ],
            ),
            # only one value kind according to value_kind
            CheckConstraint(
                name="edetail_kind_text_chk",
                check=(
                        Q(value_kind="TEXT", value_text__isnull=False) |
                        ~Q(value_kind="TEXT")
                ),
            ),
            CheckConstraint(
                name="edetail_kind_num_chk",
                check=(
                        Q(value_kind="NUM", value_num__isnull=False) |
                        ~Q(value_kind="NUM")
                ),
            ),
            CheckConstraint(
                name="edetail_kind_ts_chk",
                check=(
                        Q(value_kind="TS", value_ts__isnull=False) |
                        ~Q(value_kind="TS")
                ),
            ),
            CheckConstraint(
                name="edetail_kind_bool_chk",
                check=(
                        Q(value_kind="BOOL", value_bool__isnull=False) |
                        ~Q(value_kind="BOOL")
                ),
            ),
            CheckConstraint(
                name="edetail_kind_json_chk",
                check=(
                        Q(value_kind="JSON", value_json__isnull=False) |
                        ~Q(value_kind="JSON")
                ),
            ),
        ]
        indexes = [
            models.Index(
                name="ix_edetail_pair_current",
                fields=["entity_uuid", "detail_code"],
                condition=Q(is_current=True),
            ),
        ]

    def __str__(self):
        return f"{self.entity_uuid} :: {self.detail_code}"


class Entity(SCD2Mixin):
    """
    """
    entity_uuid = models.UUIDField(default=uuid.uuid4, db_index=True)
    type_code = models.ForeignKey(
        EntityType, on_delete=models.PROTECT, to_field="code", db_column="type_code"
    )
    display_name = models.TextField()

    # hash for ingest idempotency
    hashdiff = models.CharField(max_length=64, db_index=True)

    class Meta:
        db_table = "entity"
        constraints = [
            # Only one "current" record per entity_uid
            models.UniqueConstraint(
                fields=["entity_uuid"], condition=Q(is_current=True), name="uniq_entity_current"
            ),
            # Prohibition of interval overlaps for one entity
            ExclusionConstraint(
                name="entity_no_overlap",
                index_type="GIST",
                expressions=[
                    (F("entity_uuid"), "="),
                    (
                        models.Func(F("valid_from"), F("valid_to"), function="tstzrange"),
                        RangeOperators.OVERLAPS,
                    ),
                ],
            ),
        ]
        indexes = [
            models.Index(name="ix_entity_type_current", fields=["type_code"], condition=Q(is_current=True)),
        ]

    def __str__(self):
        return f"{self.entity_uuid} :: {self.display_name}"
