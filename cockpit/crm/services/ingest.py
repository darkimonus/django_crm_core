from typing import Mapping, Any, Optional

from .scd2 import upsert_entity, upsert_entity_detail, Result
from utils import parse_change_ts


def ingest_entity(payload: Mapping[str, Any]) -> Result:
    """
    Expected payload:
    {
      "entity_uuid": "uuid",
      "type_code": "PERSON",
      "display_name": "Acme Ltd",
      "change_ts": "2025-08-01T12:00:00Z",
      "actor": "etl@loader",               # optional
      "correlation_id": "file:batch1.csv"  # optional
    }
    """
    return upsert_entity(
        entity_uuid=payload["entity_uuid"],
        type_code=payload["type_code"],
        display_name=payload["display_name"],
        change_ts=payload["change_ts"],
        actor=payload.get("actor", "etl@loader"),
        correlation_id=payload.get("correlation_id"),
    )


def ingest_detail(payload: Mapping[str, Any]) -> Result:
    """
    Expected payload:
    {
      "entity_uuid": "uuid",
      "detail_code": "EMAIL",
      "value_kind": "TEXT|NUM|TS|BOOL|JSON",
      "value": "... or JSON object ...",
      "change_ts": "2025-08-01T12:00:00Z",
      "actor": "etl@loader",               # optional
      "correlation_id": "file:batch1.csv"  # optional
    }
    """
    return upsert_entity_detail(
        entity_uuid=payload["entity_uuid"],
        detail_code=payload["detail_code"],
        value_kind=payload["value_kind"],
        value=payload.get("value"),
        change_ts=payload["change_ts"],
        actor=payload.get("actor", "etl@loader"),
        correlation_id=payload.get("correlation_id"),
    )
