from django.urls import path, include
from rest_framework.routers import DefaultRouter

from core_agropulse.accounts.views import (
    UserViewSet,
    FarmerProfileViewSet,
    BuyerProfileViewSet,
    TransporterProfileViewSet,
)

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")
router.register(r"farmers", FarmerProfileViewSet, basename="farmer-profile")
router.register(r"buyers", BuyerProfileViewSet, basename="buyer-profile")
router.register(
    r"transporters", TransporterProfileViewSet, basename="transporter-profile"
)

app_name = "accounts"

urlpatterns = [
    path("", include(router.urls)),
]
