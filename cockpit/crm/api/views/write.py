from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from django.db import transaction

from crm.models.entities import Entity, EntityDetail
from crm.api.serializers import (
    EntitySerializer,
    EntityCreateInSerializer,
    EntityPatchInSerializer,
    DetailUpsertInSerializer,
)
from crm.services.ingest import ingest_entity, ingest_detail
from crm.services.exceptions import DomainError


class EntityCreatePatchMixin:
    def create(self, request, *args, **kwargs):
        ser = EntityCreateInSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        payload = ser.validated_data
        try:
            with transaction.atomic():
                ingest_entity({
                    "entity_uuid": str(payload["entity_uuid"]),
                    "type_code": payload["type_code"],
                    "display_name": payload["display_name"],
                    "change_ts": payload["change_ts"],
                    "actor": payload.get("actor", "api@user"),
                    "correlation_id": payload.get("correlation_id"),
                })
                for d in payload.get("details") or []:
                    dser = DetailUpsertInSerializer(data=d)
                    dser.is_valid(raise_exception=True)
                    dv = dser.validated_data
                    ingest_detail({
                        "entity_uuid": str(payload["entity_uuid"]),
                        "detail_code": dv["detail_code"],
                        "value_kind": dv["value_kind"],
                        "value": dv.get("value"),
                        "change_ts": dv.get("change_ts", payload["change_ts"]),
                        "actor": dv.get("actor", payload.get("actor", "api@user")),
                        "correlation_id": dv.get("correlation_id", payload.get("correlation_id")),
                    })
        except DomainError as e:
            raise ValidationError({"detail": str(e)})
        entity = Entity.objects.get(entity_uuid=payload["entity_uuid"], is_current=True)
        cur = list(EntityDetail.objects.filter(entity_uuid=entity.entity_uuid, is_current=True).order_by("detail_code"))
        setattr(entity, "_current_details", cur)
        return Response(EntitySerializer(entity).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, uuid=None):
        ser = EntityPatchInSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        payload = ser.validated_data
        curr = Entity.objects.filter(entity_uuid=uuid, is_current=True).select_related("type_code").first()
        if not curr:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        type_code = payload.get("type_code", curr.type_code_id)
        display_name = payload.get("display_name", curr.display_name)
        try:
            with transaction.atomic():
                ingest_entity({
                    "entity_uuid": str(uuid),
                    "type_code": type_code,
                    "display_name": display_name,
                    "change_ts": payload["change_ts"],
                    "actor": payload.get("actor", "api@user"),
                    "correlation_id": payload.get("correlation_id"),
                })
                for d in payload.get("details") or []:
                    dser = DetailUpsertInSerializer(data=d)
                    dser.is_valid(raise_exception=True)
                    dv = dser.validated_data
                    ingest_detail({
                        "entity_uuid": str(uuid),
                        "detail_code": dv["detail_code"],
                        "value_kind": dv["value_kind"],
                        "value": dv.get("value"),
                        "change_ts": dv.get("change_ts", payload["change_ts"]),
                        "actor": dv.get("actor", payload.get("actor", "api@user")),
                        "correlation_id": dv.get("correlation_id", payload.get("correlation_id")),
                    })
        except DomainError as e:
            raise ValidationError({"detail": str(e)})
        entity = Entity.objects.get(entity_uuid=uuid, is_current=True)
        cur = list(EntityDetail.objects.filter(entity_uuid=entity.entity_uuid, is_current=True).order_by("detail_code"))
        setattr(entity, "_current_details", cur)
        return Response(EntitySerializer(entity).data)
