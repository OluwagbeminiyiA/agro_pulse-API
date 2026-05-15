from django.urls import path

from core_agropulse.predictions.views import (
    BuyerReturnRecommendationView,
    DemandRecommendationView,
    RecommendationSummaryView,
    SupplierRecommendationView,
)

app_name = "predictions"

urlpatterns = [
    path(
        "predictions/recommendations/demand/",
        DemandRecommendationView.as_view(),
        name="demand-recommendation",
    ),
    path(
        "predictions/recommendations/suppliers/",
        SupplierRecommendationView.as_view(),
        name="supplier-recommendation",
    ),
    path(
        "predictions/recommendations/buyer-return/",
        BuyerReturnRecommendationView.as_view(),
        name="buyer-return-recommendation",
    ),
    path(
        "predictions/recommendations/summary/",
        RecommendationSummaryView.as_view(),
        name="recommendation-summary",
    ),
]
