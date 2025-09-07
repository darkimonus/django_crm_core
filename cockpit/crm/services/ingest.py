from typing import Mapping, Any

from .scd2 import upsert_entity, upsert_entity_detail, Result


def ingest_entity(payload: Mapping[str, Any]) -> Result:
    """Validate and upsert an Entity from a generic payload.

    Expects keys: `entity_uuid`, `type_code`, `display_name`, `change_ts`.
    Optional: `actor`, `correlation_id`. Delegates to SCD2 upsert and returns
    a `Result` with the instance and status (created/updated/noop).
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
    """Validate and upsert an EntityDetail from a generic payload.

    Expects keys: `entity_uuid`, `detail_code`, `value_kind`, `change_ts`.
    Optional: `value`, `actor`, `correlation_id`. Delegates to SCD2 upsert
    and returns a `Result` with the instance and status.
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
