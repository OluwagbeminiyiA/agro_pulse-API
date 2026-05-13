from django.urls import path, include
from rest_framework.routers import DefaultRouter

from core_agropulse.subscriptions.views import (
    SubscriptionViewSet,
    SubscriptionOrderViewSet,
    SubscriptionPaymentViewSet,
)

router = DefaultRouter()
router.register(r"subscriptions", SubscriptionViewSet, basename="subscription")
router.register(
    r"subscription-orders", SubscriptionOrderViewSet, basename="subscription-order"
)
router.register(
    r"subscription-payments",
    SubscriptionPaymentViewSet,
    basename="subscription-payment",
)

app_name = "subscriptions"

urlpatterns = [
    path("", include(router.urls)),
]
