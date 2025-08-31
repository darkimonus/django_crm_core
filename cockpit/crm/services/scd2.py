from __future__ import annotations

from typing import Any, Dict, Literal, Tuple, Optional
from dataclasses import dataclass
from django.db import transaction
from django.db.models import Q
from django.forms.models import model_to_dict

from crm.models import Entity, EntityType, EntityDetail
from utils import normalize_value, calc_hashdiff, parse_change_ts
from .exceptions import BackdatedIntervalError, TypeCodeNotFound
from .audit import write_audit


@dataclass(frozen=True)
class Result:
    instance: Any
    status: Literal["created", "updated", "noop"]


# -------- Entity (core) ---------------------------------------------------- #

def _entity_hash_components(*, type_code: str, display_name: str) -> str:
    # normalize the same way as details: TEXT
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
    Idempotent SCD2-update of Entity:
    - if there's no current version — create the first one (created);
    - if hashdiff hasn't changed — NOOP;
    - if changed — close current (valid_to=change_ts) and create new (updated).
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

    # idempotent / no-change
    if curr.hashdiff == new_hash:
        # (strict idempotency by change_ts: if the same payload came with the same ts)
        if curr.valid_from == ts:
            return Result(curr, "noop")
        # if value hasn't changed, but ts is different — also don't create new version
        return Result(curr, "noop")

    # change: check timestamp correctness
    if ts <= curr.valid_from:
        raise BackdatedIntervalError(
            f"change_ts {ts.isoformat()} must be > current.valid_from {curr.valid_from.isoformat()}"
        )

    before = _entity_public_dict(curr)

    # 1) close current
    curr.valid_to = ts
    curr.is_current = False
    curr.save(update_fields=["valid_to", "is_current", "updated_at"])

    # 2) open new
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
    return {
        "entity_uuid": str(e.entity_uuid),
        "type_code": getattr(e.type_code, "code", e.type_code_id),
        "display_name": e.display_name,
        "valid_from": e.valid_from.isoformat() if e.valid_from else None,
        "valid_to": e.valid_to.isoformat() if e.valid_to else None,
        "is_current": e.is_current,
        "hashdiff": e.hashdiff,
    }


# -------- EntityDetail (details) ------------------------------------------- #

def _detail_hash_components(*, kind: str, value: Any) -> str:
    return calc_hashdiff(normalize_value(kind, value))


@transaction.atomic
def upsert_entity_detail(
    *,
    entity_uuid,
    detail_code: str,
    value_kind: str,
    value: Any,
    change_ts,
    actor: str = "etl@loader",
    correlation_id: Optional[str] = None,
) -> Result:
    """
    Idempotent SCD2-update of EntityDetail by natural key (entity_uuid, detail_code).
    """
    ts = parse_change_ts(change_ts)
    kind = (value_kind or "").upper()
    new_hash = _detail_hash_components(kind=kind, value=value)

    curr = (
        EntityDetail.objects.select_for_update()
        .filter(entity_uuid=entity_uuid, detail_code=detail_code, is_current=True)
        .first()
    )

    payload = _detail_field_payload(kind, value)

    if curr is None:
        created = EntityDetail.objects.create(
            entity_uuid=entity_uuid,
            detail_code=detail_code,
            value_kind=kind,
            **payload,
            valid_from=ts,
            valid_to=None,
            is_current=True,
            hashdiff=new_hash,
        )
        write_audit(
            actor=actor,
            module="crm",
            entity_uuid=str(entity_uuid),
            target_kind="detail",
            target_key={"entity_uuid": str(entity_uuid), "detail_code": detail_code},
            before=None,
            after=_detail_public_dict(created),
            correlation_id=correlation_id,
        )
        return Result(created, "created")

    # idempotent/no-change
    if curr.hashdiff == new_hash:
        if curr.valid_from == ts:
            return Result(curr, "noop")
        return Result(curr, "noop")

    if ts <= curr.valid_from:
        raise BackdatedIntervalError(
            f"change_ts {ts.isoformat()} must be > current.valid_from {curr.valid_from.isoformat()}"
        )

    before = _detail_public_dict(curr)

    # 1) close current
    curr.valid_to = ts
    curr.is_current = False
    curr.save(update_fields=["valid_to", "is_current", "updated_at"])

    # 2) open new
    new_row = EntityDetail.objects.create(
        entity_uuid=entity_uuid,
        detail_code=detail_code,
        value_kind=kind,
        **payload,
        valid_from=ts,
        valid_to=None,
        is_current=True,
        hashdiff=new_hash,
    )

    write_audit(
        actor=actor,
        module="crm",
        entity_uuid=str(entity_uuid),
        target_kind="detail",
        target_key={"entity_uuid": str(entity_uuid), "detail_code": detail_code},
        before=before,
        after=_detail_public_dict(new_row),
        correlation_id=correlation_id,
    )

    return Result(new_row, "updated")


def _detail_field_payload(kind: str, value: Any) -> Dict[str, Any]:
    """
    Mapping to one of the *value_* fields according to value_kind + cleanup of others.
    """
    fields = {
        "value_text": None,
        "value_num": None,
        "value_ts": None,
        "value_bool": None,
        "value_json": None,
    }
    if kind == "TEXT":
        fields["value_text"] = normalize_value("TEXT", value) or None
    elif kind == "NUM":
        # save as Decimal as string; model casts itself
        fields["value_num"] = normalize_value("NUM", value) or None
    elif kind == "TS":
        fields["value_ts"] = parse_change_ts(value)  # normalized UTC
    elif kind == "BOOL":
        fields["value_bool"] = (str(value).lower() in {"1", "true", "yes", "y", "t"})
    elif kind == "JSON":
        # save primary JSON (ORM serializes itself), but hashdiff by canonical
        fields["value_json"] = value
    else:
        # let it fail on model CHECK constraint
        fields["value_text"] = None
    return fields


def _detail_public_dict(d: EntityDetail) -> Dict[str, Any]:
    base = {
        "entity_uuid": str(d.entity_uuid),
        "detail_code": d.detail_code,
        "value_kind": d.value_kind,
        "valid_from": d.valid_from.isoformat() if d.valid_from else None,
        "valid_to": d.valid_to.isoformat() if d.valid_to else None,
        "is_current": d.is_current,
        "hashdiff": d.hashdiff,
    }
    # for convenience in audit
    if d.value_kind == "TEXT":
        base["value_text"] = d.value_text
    elif d.value_kind == "NUM":
        base["value_num"] = str(d.value_num) if d.value_num is not None else None
    elif d.value_kind == "TS":
        base["value_ts"] = d.value_ts.isoformat() if d.value_ts else None
    elif d.value_kind == "BOOL":
        base["value_bool"] = d.value_bool
    elif d.value_kind == "JSON":
        base["value_json"] = d.value_json
    return base
