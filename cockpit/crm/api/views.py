from typing import Dict, List
from uuid import UUID

from django.db.models import Q
from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend

from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiExample

from .filters import EntitiesFilter
from crm.models.entities import Entity, EntityDetail
from crm.models.audit import AuditEvent
from crm.api.serializers import (
    EntityUpsertSerializer,
    DetailUpsertSerializer,
    EntitySerializer, EntityDetailSerializer,EntityCreateInSerializer, EntityPatchInSerializer,
)
from crm.services.ingest import ingest_entity, ingest_detail

# ---------------------------- ViewSet: Entities -----------------------------


@extend_schema_view(
    list=extend_schema(
        tags=["Entities"],
        summary="List current entities",
        # ...
    ),
    retrieve=extend_schema(
        tags=["Entities"],
        summary="Get current snapshot of a single entity",
        responses={200: EntitySerializer},
    ),
    create=extend_schema(
        tags=["Entities"],
        summary="Create first version of an entity (SCD2)",
        request=EntityCreateInSerializer,
        responses={201: EntitySerializer},
        examples=[
            OpenApiExample(
                "Create entity (with email detail)",
                value={
                    "entity_uuid": "11111111-1111-1111-1111-111111111111",
                    "type_code": "PERSON",
                    "display_name": "Alice",
                    "change_ts": "2025-08-28T10:00:00Z",
                    "details": [
                        {"detail_code": "EMAIL", "value_kind": "TEXT", "value": "alice@example.com"}
                    ]
                },
                request_only=True,
            )
        ],
    ),
    partial_update=extend_schema(
        tags=["Entities"],
        summary="Apply SCD2 update (close-and-open) to an entity",
        request=EntityPatchInSerializer,                   # <-- інший body для PATCH
        responses={200: EntitySerializer},
        examples=[
            OpenApiExample(
                "Change display_name and set phone",
                value={
                    "display_name": "Alice S.",
                    "change_ts": "2025-08-29T09:30:00Z",
                    "details": [
                        {"detail_code":"PHONE","value_kind":"TEXT","value":"+380501112233"}
                    ]
                },
                request_only=True,
            )
        ],
    ),
)
class EntityViewSet(viewsets.GenericViewSet):
    """
    Endpoints:
      - GET    /api/entities            (list current, filters, ?q= search)
      - GET    /api/entities/{uuid}     (retrieve current snapshot)
      - POST   /api/entities            (create first version; can include details[])
      - PATCH  /api/entities/{uuid}     (SCD2 update; can include details[])
      - GET    /api/entities/{uuid}/history  (combined history)
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = EntitiesFilter
    search_fields = ["display_name"]
    lookup_field = "uuid"

    def get_queryset(self):
        # current rows only by default
        return Entity.objects.filter(is_current=True).select_related("type_code")

    # -------- list --------
    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())

        include_details = request.query_params.get("include_details") in {"1", "true", "t", "yes"}
        entities = list(qs)

        if include_details:
            # attach current details per entity (minimal round-trips)
            uuids = [e.entity_uuid for e in entities]
            details = EntityDetail.objects.filter(
                entity_uuid__in=uuids, is_current=True
            )
            details_map: Dict[UUID, List[EntityDetail]] = {}
            for d in details:
                details_map.setdefault(d.entity_uuid, []).append(d)
            for e in entities:
                setattr(e, "_current_details", details_map.get(e.entity_uuid, []))

        data = EntitySerializer(entities, many=True).data
        return Response(data)

    # -------- retrieve --------
    def retrieve(self, request, uuid=None):
        entity = Entity.objects.filter(entity_uuid=uuid, is_current=True).select_related("type_code").first()
        if not entity:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        # attach current details
        cur_details = list(EntityDetail.objects.filter(entity_uuid=entity.entity_uuid, is_current=True))
        setattr(entity, "_current_details", cur_details)

        return Response(EntitySerializer(entity).data)

    # -------- create (first version) --------
    def create(self, request, *args, **kwargs):
        ser = EntityUpsertSerializer(data=request.data, context={"method": "POST"})
        ser.is_valid(raise_exception=True)
        payload = ser.validated_data

        res = ingest_entity({
            "entity_uuid": str(payload["entity_uuid"]),
            "type_code": payload["type_code"],
            "display_name": payload["display_name"],
            "change_ts": payload["change_ts"],
            "actor": payload.get("actor", "api@user"),
            "correlation_id": payload.get("correlation_id"),
        })

        # optional inline details
        details = payload.get("details") or []
        for d in details:
            details_serializer = DetailUpsertSerializer(data=d)
            details_serializer.is_valid(raise_exception=True)
            details_values = details_serializer.validated_data
            ingest_detail({
                "entity_uuid": str(payload["entity_uuid"]),
                "detail_code": details_values["detail_code"],
                "value_kind": details_values["value_kind"],
                "value": details_values.get("value"),
                "change_ts": details_values.get("change_ts", payload["change_ts"]),
                "actor": details_values.get("actor", payload.get("actor", "api@user")),
                "correlation_id": details_values.get("correlation_id", payload.get("correlation_id")),
            })

        # return current snapshot with current details
        entity = Entity.objects.get(entity_uuid=payload["entity_uuid"], is_current=True)
        cur_details = list(EntityDetail.objects.filter(entity_uuid=entity.entity_uuid, is_current=True))
        setattr(entity, "_current_details", cur_details)
        return Response(EntitySerializer(entity).data, status=status.HTTP_201_CREATED)

    # -------- partial_update (SCD2) --------
    def partial_update(self, request, uuid=None):
        ser = EntityUpsertSerializer(data=request.data, context={"method": "PATCH"})
        ser.is_valid(raise_exception=True)
        payload = ser.validated_data

        # fetch current to reuse values if omitted
        curr = Entity.objects.filter(entity_uuid=uuid, is_current=True).select_related("type_code").first()
        if not curr:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        type_code = payload.get("type_code", curr.type_code_id)
        display_name = payload.get("display_name", curr.display_name)

        ingest_entity({
            "entity_uuid": str(uuid),
            "type_code": type_code,
            "display_name": display_name,
            "change_ts": payload["change_ts"],
            "actor": payload.get("actor", "api@user"),
            "correlation_id": payload.get("correlation_id"),
        })

        # optional inline details
        details = payload.get("details") or []
        for detail in details:
            detail_serializer = DetailUpsertSerializer(data=detail)
            detail_serializer.is_valid(raise_exception=True)
            detail_values = detail_serializer.validated_data
            ingest_detail({
                "entity_uuid": str(uuid),
                "detail_code": detail_values["detail_code"],
                "value_kind": detail_values["value_kind"],
                "value": detail_values.get("value"),
                "change_ts": detail_values.get("change_ts", payload["change_ts"]),
                "actor": detail_values.get("actor", payload.get("actor", "api@user")),
                "correlation_id": detail_values.get("correlation_id", payload.get("correlation_id")),
            })

        # return updated current snapshot
        entity = Entity.objects.get(entity_uuid=uuid, is_current=True)
        cur_details = list(EntityDetail.objects.filter(entity_uuid=entity.entity_uuid, is_current=True))
        setattr(entity, "_current_details", cur_details)
        return Response(EntitySerializer(entity).data)

    # -------- history --------
    @action(detail=True, methods=["get"], url_path="history", lookup_field="uuid")
    def history(self, request, uuid: str = None):
        """
        Combined history: all entity versions + all detail versions.
        Returned as two arrays for simplicity.
        """
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


# ---------------------- Entities as-of snapshot (list) ----------------------
class EntitiesAsOfView(APIView):
    """
    GET /api/entities-asof?as_of=ISO8601[Z]&include_details=true|false
    Snapshot of entities (and optional details) valid at a given timestamp.
    """
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        as_of_raw = request.query_params.get("as_of")
        if not as_of_raw:
            return Response({"detail": "Query param 'as_of' is required."}, status=400)

        ts = parse_datetime(as_of_raw)
        if ts is None:
            return Response({"detail": "Invalid 'as_of' timestamp."}, status=400)

        # naive -> make aware in current timezone, then to UTC (Django handles it)
        if ts.tzinfo is None:
            ts = make_aware(ts)

        # [valid_from <= ts < valid_to] or valid_to IS NULL
        entities = list(
            Entity.objects.filter(
                Q(valid_from__lte=ts) & (Q(valid_to__gt=ts) | Q(valid_to__isnull=True))
            ).select_related("type_code")
        )

        include_details = request.query_params.get("include_details") in {"1", "true", "t", "yes"}
        if include_details and entities:
            uuids = [e.entity_uuid for e in entities]
            details = list(
                EntityDetail.objects.filter(
                    entity_uuid__in=uuids,
                    valid_from__lte=ts
                ).filter(Q(valid_to__gt=ts) | Q(valid_to__isnull=True))
            )
            # attach
            dmap: Dict[UUID, List[EntityDetail]] = {}
            for detail in details:
                dmap.setdefault(detail.entity_uuid, []).append(detail)
            for entity in entities:
                setattr(entity, "_asof_details", dmap.get(entity.entity_uuid, []))

        return Response(EntitySerializer(entities, many=True).data)


# ------------------------------ Diff (audit) --------------------------------
class DiffView(APIView):
    """
    GET /api/diff?from=YYYY-MM-DD&to=YYYY-MM-DD
    Returns audit events within [from, to] inclusive (simple list for MVP).
    """
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        from_s = request.query_params.get("from")
        to_s = request.query_params.get("to")
        if not from_s or not to_s:
            return Response({"detail": "Query params 'from' and 'to' are required."}, status=400)

        fts = parse_datetime(from_s) or parse_datetime(from_s + "T00:00:00Z")
        tts = parse_datetime(to_s) or parse_datetime(to_s + "T23:59:59Z")
        if fts is None or tts is None:
            return Response({"detail": "Invalid 'from' or 'to' timestamp."}, status=400)

        qs = AuditEvent.objects.filter(happened_at__gte=fts, happened_at__lte=tts).order_by("happened_at")
        data = [{
            "happened_at": a.happened_at,
            "actor": a.actor,
            "module": a.module,
            "entity_uuid": str(a.entity_uuid) if a.entity_uuid else None,
            "target_kind": a.target_kind,
            "target_key": a.target_key,
            "before": a.before,
            "after": a.after,
            "correlation_id": a.correlation_id,
        } for a in qs]
        return Response(data)
