from __future__ import annotations

from typing import Any, Dict, Optional
from django.db import transaction

from crm.models import Entity, EntityType
from utils import normalize_value, calc_hashdiff, parse_change_ts
from crm.services.exceptions import BackdatedIntervalError, TypeCodeNotFound
from crm.services.audit import write_audit
from .types import Result


def _entity_hash_components(*, type_code: str, display_name: str) -> str:
    """
    Build a stable hash from normalized business fields for idempotency.
    """
    return calc_hashdiff(
        normalize_value("TEXT", type_code),
        normalize_value("TEXT", display_name),
    )


@transaction.atomic
def upsert_entity(
    *,
    entity_uuid,
    type_code: str,
    display_name: str,
    change_ts,
    actor: str = "etl@loader",
    correlation_id: Optional[str] = None,
) -> Result:
    """
    SCD2 upsert for Entity.

    Creates the first version when absent; otherwise compares the hashdiff and
    either no-ops or closes the current row and opens a new one at `change_ts`.
    Writes an audit event for created/updated transitions.
    """
    ts = parse_change_ts(change_ts)

    et = EntityType.objects.filter(code=type_code).only("code").first()
    if not et:
        raise TypeCodeNotFound(f"type_code '{type_code}' is not in EntityType")

    new_hash = _entity_hash_components(type_code=type_code, display_name=display_name)

    curr = (
        Entity.objects.select_for_update()
        .filter(entity_uuid=entity_uuid, is_current=True)
        .first()
    )

    if curr is None:
        created = Entity.objects.create(
            entity_uuid=entity_uuid,
            type_code=et,
            display_name=display_name,
            valid_from=ts,
            valid_to=None,
            is_current=True,
            hashdiff=new_hash,
        )
        write_audit(
            actor=actor,
            module="crm",
            entity_uuid=str(entity_uuid),
            target_kind="entity",
            target_key={"entity_uuid": str(entity_uuid)},
            before=None,
            after=_entity_public_dict(created),
            correlation_id=correlation_id,
        )
        return Result(created, "created")

    if curr.hashdiff == new_hash:
        if curr.valid_from == ts:
            return Result(curr, "noop")
        return Result(curr, "noop")

    if ts <= curr.valid_from:
        raise BackdatedIntervalError(
            f"change_ts {ts.isoformat()} must be > current.valid_from {curr.valid_from.isoformat()}"
        )

    before = _entity_public_dict(curr)
    curr.valid_to = ts
    curr.is_current = False
    curr.save(update_fields=["valid_to", "is_current", "updated_at"])

    new_row = Entity.objects.create(
        entity_uuid=entity_uuid,
        type_code=et,
        display_name=display_name,
        valid_from=ts,
        valid_to=None,
        is_current=True,
        hashdiff=new_hash,
    )

    write_audit(
        actor=actor,
        module="crm",
        entity_uuid=str(entity_uuid),
        target_kind="entity",
        target_key={"entity_uuid": str(entity_uuid)},
        before=before,
        after=_entity_public_dict(new_row),
        correlation_id=correlation_id,
    )

    return Result(new_row, "updated")


def _entity_public_dict(e: Entity) -> Dict[str, Any]:
    """
    Serialize Entity to an audit/public-facing dict (no model internals).
    """
    return {
        "entity_uuid": str(e.entity_uuid),
        "type_code": getattr(e.type_code, "code", e.type_code_id),
        "display_name": e.display_name,
        "valid_from": e.valid_from.isoformat() if e.valid_from else None,
        "valid_to": e.valid_to.isoformat() if e.valid_to else None,
        "is_current": e.is_current,
        "hashdiff": e.hashdiff,
    }
