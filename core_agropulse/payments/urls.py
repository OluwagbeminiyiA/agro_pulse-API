from django.urls import path, include
from rest_framework.routers import DefaultRouter

from core_agropulse.payments.views import (
    PaymentViewSet,
    EscrowAccountViewSet,
    PaymentSplitViewSet,
    PayoutViewSet,
)

router = DefaultRouter()
router.register(r"payments", PaymentViewSet, basename="payment")
router.register(r"escrow", EscrowAccountViewSet, basename="escrow")
router.register(r"payment-splits", PaymentSplitViewSet, basename="payment-split")
router.register(r"payouts", PayoutViewSet, basename="payout")

app_name = "payments"

urlpatterns = [
    path("", include(router.urls)),
]
