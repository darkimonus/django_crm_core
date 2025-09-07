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
    """Persist a business audit event.

    Records who did what and when at the domain level, storing a target
    identifier with "before" and "after" payloads. Intended to be called
    inside the same transaction as the state-changing operation.
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
    """Extract a typed value from an audit payload into a single Python value.

    Accepts a mapping with a `value_kind` discriminator and returns the
    corresponding `value_*` field (TEXT/NUM/TS/BOOL/JSON). Returns None for
    empty payloads and the original mapping for unknown kinds.
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
