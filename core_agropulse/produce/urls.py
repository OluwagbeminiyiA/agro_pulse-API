from django.urls import path, include
from rest_framework.routers import DefaultRouter

from core_agropulse.produce.views import ProduceViewSet

router = DefaultRouter()
router.register(r"produces", ProduceViewSet, basename="produce")

app_name = "produce"

urlpatterns = [
    path("", include(router.urls)),
]
