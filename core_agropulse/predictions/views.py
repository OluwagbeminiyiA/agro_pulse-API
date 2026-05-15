from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core_agropulse.accounts.models import BuyerProfile
from core_agropulse.predictions.services import PredictionEngineService
from core_agropulse.produce.models import Produce


def _demand_forecast_payload(forecast):
    return {
        "id": str(forecast.id),
        "produce_id": str(forecast.produce_id),
        "predicted_demand_volume": forecast.predicted_demand_volume,
        "forecast_period": forecast.forecast_period,
        "demand_spike_probability": str(forecast.demand_spike_probability),
        "recommended_stock_level": forecast.recommended_stock_level,
        "generated_at": forecast.generated_at,
    }


def _buyer_prediction_payload(prediction_result):
    prediction = prediction_result.prediction
    return {
        "id": str(prediction.id),
        "buyer_id": str(prediction.buyer_id_id),
        "produce_id": str(prediction.produce_id_id),
        "predicted_return_date": prediction.predicted_return_date,
        "predicted_quantity": prediction.predicted_quantity,
        "return_probability": str(prediction.return_probability),
        "buyer_category": prediction.buyer_category,
        "confidence": str(prediction_result.confidence),
        "signals": prediction_result.signals,
        "generated_at": prediction.generated_at,
    }


class DemandRecommendationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        produce_id = request.query_params.get("produce_id")
        forecast_period = request.query_params.get("forecast_period", "weekly")

        if not produce_id:
            return Response(
                {"detail": "produce_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            produce = Produce.objects.get(id=produce_id)
        except Produce.DoesNotExist:
            return Response(
                {"detail": "Produce not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        forecast = PredictionEngineService.generate_demand_forecast(
            produce=produce,
            forecast_period=forecast_period,
        )

        return Response({"demand_forecast": _demand_forecast_payload(forecast)})


class SupplierRecommendationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        buyer_id = request.query_params.get("buyer_id")
        produce_id = request.query_params.get("produce_id")
        quantity_required = int(request.query_params.get("quantity_required", 1))
        limit = int(request.query_params.get("limit", 5))

        if not buyer_id or not produce_id:
            return Response(
                {"detail": "buyer_id and produce_id are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            buyer = BuyerProfile.objects.get(id=buyer_id)
        except BuyerProfile.DoesNotExist:
            return Response(
                {"detail": "Buyer profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            produce = Produce.objects.get(id=produce_id)
        except Produce.DoesNotExist:
            return Response(
                {"detail": "Produce not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        recommendations = PredictionEngineService.recommend_suppliers(
            buyer=buyer,
            produce=produce,
            quantity_required=max(1, quantity_required),
            limit=max(1, min(limit, 20)),
        )

        return Response(
            {
                "buyer_id": str(buyer.id),
                "produce_id": str(produce.id),
                "recommendations": recommendations,
            }
        )


class BuyerReturnRecommendationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        buyer_id = request.query_params.get("buyer_id")
        produce_id = request.query_params.get("produce_id")

        if not buyer_id or not produce_id:
            return Response(
                {"detail": "buyer_id and produce_id are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            buyer = BuyerProfile.objects.get(id=buyer_id)
        except BuyerProfile.DoesNotExist:
            return Response(
                {"detail": "Buyer profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            produce = Produce.objects.get(id=produce_id)
        except Produce.DoesNotExist:
            return Response(
                {"detail": "Produce not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        prediction_result = PredictionEngineService.generate_buyer_return_prediction(
            buyer=buyer,
            produce=produce,
        )

        return Response(
            {"buyer_return_prediction": _buyer_prediction_payload(prediction_result)}
        )


class RecommendationSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        buyer_id = request.query_params.get("buyer_id")
        produce_id = request.query_params.get("produce_id")
        forecast_period = request.query_params.get("forecast_period", "weekly")

        if not buyer_id or not produce_id:
            return Response(
                {"detail": "buyer_id and produce_id are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            buyer = BuyerProfile.objects.get(id=buyer_id)
        except BuyerProfile.DoesNotExist:
            return Response(
                {"detail": "Buyer profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            produce = Produce.objects.get(id=produce_id)
        except Produce.DoesNotExist:
            return Response(
                {"detail": "Produce not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        demand_forecast = PredictionEngineService.generate_demand_forecast(
            produce=produce,
            forecast_period=forecast_period,
        )
        buyer_return_prediction = (
            PredictionEngineService.generate_buyer_return_prediction(
                buyer=buyer,
                produce=produce,
            )
        )
        supplier_recommendations = PredictionEngineService.recommend_suppliers(
            buyer=buyer,
            produce=produce,
            quantity_required=buyer_return_prediction.prediction.predicted_quantity,
            limit=5,
        )

        return Response(
            {
                "demand_forecast": _demand_forecast_payload(demand_forecast),
                "buyer_return_prediction": _buyer_prediction_payload(
                    buyer_return_prediction
                ),
                "supplier_recommendations": supplier_recommendations,
            }
        )
