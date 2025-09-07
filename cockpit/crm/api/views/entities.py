from rest_framework import viewsets
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiExample, OpenApiParameter
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from crm.api.filters import EntitiesFilter
from .read import EntityListRetrieveMixin
from .write import EntityCreatePatchMixin
from crm.api.serializers import EntitySerializer, EntityCreateInSerializer, EntityPatchInSerializer


@extend_schema_view(
    list=extend_schema(
        tags=["Entities"],
        summary="List current entities",
        parameters=[
            OpenApiParameter(
                name="search",
                required=False,
                type=str,
                location=OpenApiParameter.QUERY,
                description="Search in display_name",
            ),
            OpenApiParameter(
                name="type",
                required=False,
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter by type code",
            ),
            OpenApiParameter(
                name="detail_code",
                required=False,
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter by detail code (e.g. EMAIL)",
            ),
            OpenApiParameter(
                name="detail_value",
                required=False,
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter by detail value; omit for presence-only",
            ),
            OpenApiParameter(
                name="detail_value_kind",
                required=False,
                type=str,
                location=OpenApiParameter.QUERY,
                description="TEXT|NUM|BOOL|TS|JSON",
            ),
            OpenApiParameter(
                name="include_details",
                required=False,
                type=bool,
                location=OpenApiParameter.QUERY,
                description="Include current details",
            ),
        ],
        responses={200: EntitySerializer(many=True)},
        examples=[
            OpenApiExample(
                name="Entities list (simple)",
                summary="List with one entity (no details)",
                value=[
                    {
                        "entity_uuid": "550e8400-e29b-41d4-a716-446655440001",
                        "type_code": "PERSON",
                        "display_name": "John Doe",
                        "valid_from": "2025-01-15T10:30:00Z",
                        "valid_to": None,
                        "is_current": True,
                        "hashdiff": "..."
                    }
                ],
            ),
            OpenApiExample(
                name="Entities list (with details)",
                summary="List with details included",
                value=[
                    {
                        "entity_uuid": "11111111-1111-1111-1111-111111111111",
                        "type_code": "PERSON",
                        "display_name": "Alice S.",
                        "valid_from": "2025-08-29T09:30:00Z",
                        "valid_to": None,
                        "is_current": True,
                        "hashdiff": "...",
                        "details": [
                            {
                                "entity_uuid": "11111111-1111-1111-1111-111111111111",
                                "detail_code": "EMAIL",
                                "value_kind": "TEXT",
                                "value_text": "alice@example.com",
                                "valid_from": "2025-08-29T09:30:00Z",
                                "valid_to": None,
                                "is_current": True,
                                "hashdiff": "..."
                            }
                        ]
                    }
                ],
            ),
        ],
    ),
    retrieve=extend_schema(
        tags=["Entities"],
        summary="Get current entity",
        responses={200: EntitySerializer}
    ),
    create=extend_schema(
        tags=["Entities"],
        summary="Create first version (SCD2)",
        request=EntityCreateInSerializer,
        responses={201: EntitySerializer},
        examples=[
            OpenApiExample(
                "Create entity (with email)",
                value={
                    "entity_uuid": "11111111-1111-1111-1111-111111111111",
                    "type_code": "PERSON",
                    "display_name": "Alice",
                    "change_ts": "2025-08-28T10:00:00Z",
                    "details": [
                        {
                            "detail_code": "EMAIL",
                            "value_kind": "TEXT",
                            "value": "alice@example.com",
                        }
                    ],
                },
            )
        ],
    ),
    partial_update=extend_schema(
        tags=["Entities"],
        summary="SCD2 update",
        request=EntityPatchInSerializer,
        responses={200: EntitySerializer},
    ),
)
class EntityViewSet(EntityListRetrieveMixin, EntityCreatePatchMixin, viewsets.GenericViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = EntitiesFilter
    search_fields = ["display_name"]
    lookup_field = "uuid"
