from django.urls import path, include
from rest_framework.routers import DefaultRouter

from crm.api.views.entities import EntityViewSet
from crm.api.views.asof import EntitiesAsOfView
from crm.api.views.diff import DiffView

app_name = "crm"

router = DefaultRouter()
router.register(r"entities", EntityViewSet, basename="entities")

urlpatterns = [
    path("", include(router.urls)),
    path("entities-asof/", EntitiesAsOfView.as_view(), name="entities-asof"),
    path("diff/", DiffView.as_view(), name="entities-diff"),
]
