from django.urls import path, include
from rest_framework.routers import DefaultRouter

from core_agropulse.delivery.views import DeliveryViewSet, RiderEarningsViewSet

router = DefaultRouter()
router.register(r"deliveries", DeliveryViewSet, basename="delivery")
router.register(r"rider-earnings", RiderEarningsViewSet, basename="rider-earnings")

app_name = "delivery"

urlpatterns = [
    path("", include(router.urls)),
]
