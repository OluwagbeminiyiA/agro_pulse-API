from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core_agropulse.predictions.models import BuyerBehaviorPrediction, DemandForecast


def _buyer_prediction_payload(prediction):
    return {
        "id": str(prediction.id),
        "buyer_id": str(prediction.buyer_id_id),
        "produce_id": str(prediction.produce_id_id),
        "predicted_return_date": prediction.predicted_return_date,
        "predicted_quantity": prediction.predicted_quantity,
        "return_probability": str(prediction.return_probability),
        "buyer_category": prediction.buyer_category,
        "created_at": prediction.created_at,
        "generated_at": prediction.generated_at,
    }


def _demand_forecast_payload(forecast):
    return {
        "id": str(forecast.id),
        "produce_id": str(forecast.produce_id),
        "predicted_demand_volume": forecast.predicted_demand_volume,
        "forecast_period": forecast.forecast_period,
        "demand_spike_probability": str(forecast.demand_spike_probability),
        "recommended_stock_level": forecast.recommended_stock_level,
        "created_at": forecast.created_at,
        "generated_at": forecast.generated_at,
    }


def _latest_buyer_prediction(buyer_id=None, produce_id=None):
    queryset = BuyerBehaviorPrediction.objects.select_related("buyer_id", "produce_id")

    if buyer_id is not None:
        queryset = queryset.filter(buyer_id=buyer_id)

    if produce_id is not None:
        queryset = queryset.filter(produce_id=produce_id)

    return queryset.first()


def _latest_demand_forecast(produce_id=None):
    queryset = DemandForecast.objects.select_related("produce")

    if produce_id is not None:
        queryset = queryset.filter(produce_id=produce_id)

    return queryset.first()


class BuyerReturnPredictionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        buyer_id = request.query_params.get("buyer_id")
        produce_id = request.query_params.get("produce_id")

        prediction = _latest_buyer_prediction(buyer_id=buyer_id, produce_id=produce_id)
        if prediction is None:
            return Response(
                {"detail": "No buyer return prediction found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response({"prediction": _buyer_prediction_payload(prediction)})


class QuantityForecastView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        buyer_id = request.query_params.get("buyer_id")
        produce_id = request.query_params.get("produce_id")

        prediction = _latest_buyer_prediction(buyer_id=buyer_id, produce_id=produce_id)
        if prediction is None:
            return Response(
                {"detail": "No quantity forecast found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {
                "buyer_id": str(prediction.buyer_id_id),
                "produce_id": str(prediction.produce_id_id),
                "predicted_quantity": prediction.predicted_quantity,
                "predicted_return_date": prediction.predicted_return_date,
                "generated_at": prediction.generated_at,
            }
        )


class DemandSpikeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        produce_id = request.query_params.get("produce_id")

        forecast = _latest_demand_forecast(produce_id=produce_id)
        if forecast is None:
            return Response(
                {"detail": "No demand spike forecast found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response({"forecast": _demand_forecast_payload(forecast)})


class ForecastSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        buyer_id = request.query_params.get("buyer_id")
        produce_id = request.query_params.get("produce_id")

        buyer_prediction = _latest_buyer_prediction(
            buyer_id=buyer_id, produce_id=produce_id
        )
        demand_forecast = _latest_demand_forecast(produce_id=produce_id)

        if buyer_prediction is None and demand_forecast is None:
            return Response(
                {"detail": "No forecast data available."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {
                "buyer_return_prediction": _buyer_prediction_payload(buyer_prediction)
                if buyer_prediction
                else None,
                "demand_forecast": _demand_forecast_payload(demand_forecast)
                if demand_forecast
                else None,
            }
        )


class RecommendationEngineView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        produce_id = request.query_params.get("produce_id")

        if not produce_id:
            return Response(
                {"detail": "produce_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        demand_forecast = _latest_demand_forecast(produce_id=produce_id)
        if demand_forecast is None:
            return Response(
                {"detail": "No recommendation data found for the selected produce."},
                status=status.HTTP_404_NOT_FOUND,
            )

        spike_probability = float(demand_forecast.demand_spike_probability)
        if spike_probability >= 70:
            recommendation = (
                "Increase stock aggressively and prepare for a demand surge."
            )
            action = "increase_stock"
        elif spike_probability >= 40:
            recommendation = (
                "Monitor stock closely and replenish before the next forecast cycle."
            )
            action = "monitor_stock"
        else:
            recommendation = (
                "Maintain current stock levels and continue routine monitoring."
            )
            action = "maintain_stock"

        buyer_prediction = _latest_buyer_prediction(produce_id=produce_id)

        return Response(
            {
                "produce_id": produce_id,
                "recommended_action": action,
                "recommendation": recommendation,
                "suggested_stock_level": demand_forecast.recommended_stock_level,
                "demand_forecast": _demand_forecast_payload(demand_forecast),
                "buyer_return_prediction": _buyer_prediction_payload(buyer_prediction)
                if buyer_prediction
                else None,
            }
        )
