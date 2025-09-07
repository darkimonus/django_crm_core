from typing import Dict, List
from uuid import UUID

from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

from crm.models.entities import Entity, EntityDetail
from crm.api.serializers import (
    EntitySerializer,
    EntityDetailSerializer,
    HistoryResponseSerializer,
)


class EntityListRetrieveMixin:
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return Entity.objects.filter(is_current=True).select_related("type_code")

    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        raw_inc = request.query_params.get("include_details")
        match (str(raw_inc).lower() if raw_inc is not None else ""):
            case "1" | "true" | "t" | "yes" | "y":
                include_details = True
            case _:
                include_details = False

        entities = list(qs)
        if include_details:
            uuids = [e.entity_uuid for e in entities]
            details = EntityDetail.objects.filter(
                entity_uuid__in=uuids, is_current=True
            ).order_by("detail_code")
            dmap: Dict[UUID, List[EntityDetail]] = {}
            for d in details:
                dmap.setdefault(d.entity_uuid, []).append(d)
            for e in entities:
                setattr(e, "_current_details", dmap.get(e.entity_uuid, []))
        return Response(EntitySerializer(entities, many=True).data)

    def retrieve(self, request, uuid=None):
        entity = Entity.objects.filter(entity_uuid=uuid, is_current=True).select_related("type_code").first()
        if not entity:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        cur_details = list(
            EntityDetail.objects.filter(entity_uuid=entity.entity_uuid, is_current=True).order_by("detail_code")
        )
        setattr(entity, "_current_details", cur_details)
        return Response(EntitySerializer(entity).data)

    @extend_schema(
        tags=["Entities"],
        summary="Entity + details SCD2 history",
        description=(
                "Returns the full SCD2 timeline for the entity and all detail codes, "
                "ordered chronologically by valid_from. No query filters are supported; "
                "use list/as-of endpoints for filtered views."
        ),
        parameters=[
            OpenApiParameter(
                name="uuid",
                location=OpenApiParameter.PATH,
                required=True,
                type=OpenApiTypes.UUID,
                description="Business UUID of the entity (path parameter)",
            )
        ],
        responses={200: HistoryResponseSerializer},
        examples=[
            OpenApiExample(
                name="History response example",
                summary="Chronological versions for entity and details",
                value={
                    "entity": [
                        {
                            "entity_uuid": "11111111-1111-1111-1111-111111111111",
                            "type_code": "PERSON",
                            "display_name": "Alice",
                            "valid_from": "2025-08-28T10:00:00Z",
                            "valid_to": "2025-08-29T09:30:00Z",
                            "is_current": False,
                            "hashdiff": "..."
                        },
                        {
                            "entity_uuid": "11111111-1111-1111-1111-111111111111",
                            "type_code": "PERSON",
                            "display_name": "Alice S.",
                            "valid_from": "2025-08-29T09:30:00Z",
                            "valid_to": None,
                            "is_current": True,
                            "hashdiff": "..."
                        }
                    ],
                    "details": [
                        {
                            "entity_uuid": "11111111-1111-1111-1111-111111111111",
                            "detail_code": "EMAIL",
                            "value_kind": "TEXT",
                            "value_text": "alice@example.com",
                            "valid_from": "2025-08-28T10:00:00Z",
                            "valid_to": None,
                            "is_current": True,
                            "hashdiff": "..."
                        }
                    ]
                },
            )
        ],
    )
    @action(detail=True, methods=["get"], url_path="history", lookup_field="uuid")
    def history(self, request, uuid: str = None):
        entity_versions = list(
            Entity.objects.filter(entity_uuid=uuid).order_by("valid_from").select_related("type_code")
        )
        details_versions = list(
            EntityDetail.objects.filter(entity_uuid=uuid).order_by("detail_code", "valid_from")
        )
        return Response({
            "entity": EntitySerializer(entity_versions, many=True).data,
            "details": EntityDetailSerializer(details_versions, many=True).data,
        })
