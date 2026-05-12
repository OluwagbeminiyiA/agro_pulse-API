from django.urls import path, include
from rest_framework.routers import DefaultRouter

from core_agropulse.orders.views import OrderViewSet, OrderItemViewSet

router = DefaultRouter()
router.register(r"orders", OrderViewSet, basename="order")
router.register(r"order-items", OrderItemViewSet, basename="order-item")

app_name = "orders"

urlpatterns = [
    path("", include(router.urls)),
]
