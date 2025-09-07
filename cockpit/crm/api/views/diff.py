from django.utils.dateparse import parse_datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from django.utils.timezone import make_aware

from crm.models.audit import AuditEvent
from crm.services.audit import unified_value
from crm.api.serializers import DiffGroupOutSerializer


class DiffView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    @extend_schema(
        tags=["Entities", "History"],
        summary="List of changes grouped by entity and field",
        parameters=[
            OpenApiParameter(
                name="from",
                required=True,
                type=str,
                location=OpenApiParameter.QUERY,
                description="Start ISO8601 (inclusive)",
                examples=[
                    OpenApiExample(
                        name="date-only",
                        summary="Common default start",
                        value="2025-01-01",
                    ),
                    OpenApiExample(
                        name="with-time",
                        summary="Explicit start timestamp",
                        value="2025-01-01T00:00:00Z",
                    ),
                ],
            ),
            OpenApiParameter(
                name="to",
                required=True,
                type=str,
                location=OpenApiParameter.QUERY,
                description="End ISO8601 (inclusive)",
                examples=[
                    OpenApiExample(
                        name="date-only",
                        summary="Common default end",
                        value="2025-12-31",
                    ),
                    OpenApiExample(
                        name="with-time",
                        summary="Explicit end timestamp",
                        value="2025-12-31T23:59:59Z",
                    ),
                ],
            ),
        ],
        responses={200: DiffGroupOutSerializer(many=True)},
        examples=[
            OpenApiExample(
                name="Grouped diff example",
                summary="Grouped by entity and field",
                value=[
                    {
                        "entity_uuid": "11111111-1111-1111-1111-111111111111",
                        "field": "display_name",
                        "changes": [
                            {
                                "happened_at": "2025-08-29T09:30:01Z",
                                "actor": "api@user",
                                "before": "Alice",
                                "after": "Alice S.",
                                "correlation_id": "job-123"
                            }
                        ]
                    },
                    {
                        "entity_uuid": "11111111-1111-1111-1111-111111111111",
                        "field": "EMAIL",
                        "changes": [
                            {
                                "happened_at": "2025-08-29T09:31:00Z",
                                "actor": "api@user",
                                "before": "alice@old.com",
                                "after": "alice@example.com",
                                "correlation_id": "job-123"
                            }
                        ]
                    }
                ],
            )
        ],
    )
    def get(self, request):
        from_s = request.query_params.get("from")
        to_s = request.query_params.get("to")
        if not from_s or not to_s:
            return Response({"detail": "Query params 'from' and 'to' are required."}, status=400)
        fts = parse_datetime(from_s) or parse_datetime(from_s + "T00:00:00Z")
        tts = parse_datetime(to_s) or parse_datetime(to_s + "T23:59:59Z")
        if fts is None or tts is None:
            return Response({"detail": "Invalid 'from' or 'to' timestamp."}, status=400)
        if fts.tzinfo is None:
            fts = make_aware(fts)
        if tts.tzinfo is None:
            tts = make_aware(tts)
        events = AuditEvent.objects.filter(
            happened_at__gte=fts, happened_at__lte=tts
        ).order_by("happened_at")

        groups = {}
        for a in events:
            eid = str(a.entity_uuid) if a.entity_uuid else str(a.target_key.get("entity_uuid"))
            match a.target_kind:
                case "entity":
                    before = a.before or {}
                    after = a.after or {}
                    for fld in ("type_code", "display_name"):
                        if before.get(fld) != after.get(fld):
                            key = (eid, fld)
                            groups.setdefault(key, []).append({
                                "happened_at": a.happened_at,
                                "actor": a.actor,
                                "before": before.get(fld),
                                "after": after.get(fld),
                                "correlation_id": a.correlation_id,
                            })
                case "detail":
                    code = a.target_key.get("detail_code") or "DETAIL"
                    key = (eid, code)
                    groups.setdefault(key, []).append({
                        "happened_at": a.happened_at,
                        "actor": a.actor,
                        "before": unified_value(a.before),
                        "after": unified_value(a.after),
                        "correlation_id": a.correlation_id,
                    })
                case _:
                    # ignore unknown kinds for now
                    pass

        result = [
            {"entity_uuid": k[0], "field": k[1], "changes": v}
            for k, v in groups.items()
        ]
        return Response(result)
