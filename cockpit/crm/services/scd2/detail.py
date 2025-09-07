from __future__ import annotations

from typing import Any, Dict, Optional
from django.db import transaction

from crm.models import EntityDetail
from utils import normalize_value, calc_hashdiff, parse_change_ts
from crm.services.exceptions import BackdatedIntervalError
from crm.services.audit import write_audit
from .types import Result


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

    if curr.hashdiff == new_hash:
        if curr.valid_from == ts:
            return Result(curr, "noop")
        return Result(curr, "noop")

    if ts <= curr.valid_from:
        raise BackdatedIntervalError(
            f"change_ts {ts.isoformat()} must be > current.valid_from {curr.valid_from.isoformat()}"
        )

    before = _detail_public_dict(curr)
    curr.valid_to = ts
    curr.is_current = False
    curr.save(update_fields=["valid_to", "is_current", "updated_at"])

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
    fields = {
        "value_text": None,
        "value_num": None,
        "value_ts": None,
        "value_bool": None,
        "value_json": None,
    }
    match kind:
        case "TEXT":
            fields["value_text"] = normalize_value("TEXT", value) or None
        case "NUM":
            fields["value_num"] = normalize_value("NUM", value) or None
        case "TS":
            fields["value_ts"] = parse_change_ts(value)
        case "BOOL":
            fields["value_bool"] = (str(value).lower() in {"1", "true", "yes", "y", "t"})
        case "JSON":
            fields["value_json"] = value
        case _:
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
    match d.value_kind:
        case "TEXT":
            base["value_text"] = d.value_text
        case "NUM":
            base["value_num"] = str(d.value_num) if d.value_num is not None else None
        case "TS":
            base["value_ts"] = d.value_ts.isoformat() if d.value_ts else None
        case "BOOL":
            base["value_bool"] = d.value_bool
        case "JSON":
            base["value_json"] = d.value_json
        case _:
            pass
    return base
