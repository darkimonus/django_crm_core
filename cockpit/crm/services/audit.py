from typing import Optional, Mapping, Any

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


def unified_value(d: Optional[Mapping[str, Any]]) -> Any:
    """Return a unified Python value from an audit value payload.

    The payload is expected to be a mapping that may contain
    `value_kind` and one of `value_text`, `value_num`, `value_ts`,
    `value_bool`, or `value_json`.
    """
    if not d:
        return None
    kind = d.get("value_kind")
    match kind:
        case "TEXT":
            return d.get("value_text")
        case "NUM":
            return d.get("value_num")
        case "TS":
            return d.get("value_ts")
        case "BOOL":
            return d.get("value_bool")
        case "JSON":
            return d.get("value_json")
        case _:
            return d
