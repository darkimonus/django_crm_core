from django.db import models


class AuditEvent(models.Model):
    """
    Centralized business audit.
    """
    happened_at = models.DateTimeField(auto_now_add=True)
    actor = models.CharField(max_length=200)
    module = models.CharField(max_length=50, default="crm")
    entity_uuid = models.UUIDField(null=True, blank=True)

    target_kind = models.CharField(max_length=80)
    target_key = models.JSONField()
    before = models.JSONField(null=True, blank=True)
    after = models.JSONField(null=True, blank=True)
    correlation_id = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        db_table = "audit_event"
        indexes = [
            models.Index(fields=["entity_uuid"]),
            models.Index(fields=["module", "target_kind"]),
        ]
