from typing import Optional, Mapping, Any

from django.db import transaction

from crm.models import AuditEvent


def write_audit(
    *,
    actor: str,
    module: str,
    entity_uuid: Optional[str],
    target_kind: str,
    target_key: Mapping[str, Any],
    before: Optional[Mapping[str, Any]],
    after: Optional[Mapping[str, Any]],
    correlation_id: Optional[str] = None,
) -> None:
    """
    Business audit record (before/after). Call inside update transaction.
    """
    # no heavy validation here — this is a convenient call layer
    AuditEvent.objects.create(
        actor=actor or "system",
        module=module or "crm",
        entity_uuid=entity_uuid,
        target_kind=target_kind,
        target_key=target_key,
        before=before,
        after=after,
        correlation_id=correlation_id,
    )
