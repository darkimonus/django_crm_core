from django.db import models
from django.db.models import Q, F, CheckConstraint


class SCD2Mixin(models.Model):
    """
    Abstract SCD2 base model.
    """
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField(null=True, blank=True)
    is_current = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        constraints = [
            CheckConstraint(
                name="scd2_valid_bounds_chk",
                condition=Q(valid_from__lt=F("valid_to")) | Q(valid_to__isnull=True),
            ),
            CheckConstraint(
                name="scd2_current_to_null_chk",
                condition=(Q(is_current=True, valid_to__isnull=True) |
                           Q(is_current=False, valid_to__isnull=False)),
            ),
        ]
