from typing import Dict, List
from uuid import UUID

from django.db.models import Q
from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from drf_spectacular.utils import extend_schema, OpenApiParameter

from crm.models.entities import Entity, EntityDetail
from crm.api.serializers import EntitySerializer


class EntitiesAsOfView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    @extend_schema(
        tags=["Entities"],
        summary="As-of snapshot",
        parameters=[
            OpenApiParameter(
                name="as_of",
                required=True,
                type=str,
                location=OpenApiParameter.QUERY,
                description=(
                    "ISO8601 timestamp; rows with valid_from <= ts < valid_to "
                    "or open-ended"
                ),
            ),
            OpenApiParameter(
                name="include_details",
                required=False,
                type=bool,
                location=OpenApiParameter.QUERY,
                description="Include details valid at as_of",
            ),
        ],
        responses={200: EntitySerializer(many=True)},
    )
    def get(self, request):
        as_of_raw = request.query_params.get("as_of")
        if not as_of_raw:
            return Response({"detail": "Query param 'as_of' is required."}, status=400)
        ts = parse_datetime(as_of_raw)
        if ts is None:
            return Response({"detail": "Invalid 'as_of' timestamp."}, status=400)
        if ts.tzinfo is None:
            ts = make_aware(ts)

        entities = list(
            Entity.objects.filter(
                Q(valid_from__lte=ts)
                & (Q(valid_to__gt=ts) | Q(valid_to__isnull=True))
            ).select_related("type_code")
        )

        raw_inc = request.query_params.get("include_details")
        match (str(raw_inc).lower() if raw_inc is not None else ""):
            case "1" | "true" | "t" | "yes" | "y":
                include_details = True
            case _:
                include_details = False

        if include_details and entities:
            uuids = [e.entity_uuid for e in entities]
            details = list(
                EntityDetail.objects.filter(
                    entity_uuid__in=uuids, valid_from__lte=ts
                ).filter(Q(valid_to__gt=ts) | Q(valid_to__isnull=True))
            )
            dmap: Dict[UUID, List[EntityDetail]] = {}
            for detail in details:
                dmap.setdefault(detail.entity_uuid, []).append(detail)
            for entity in entities:
                setattr(entity, "_asof_details", dmap.get(entity.entity_uuid, []))
        return Response(EntitySerializer(entities, many=True).data)
