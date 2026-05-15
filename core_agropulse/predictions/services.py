from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal
from statistics import mean

from django.db.models import Avg, Q, Sum
from django.utils import timezone

from core_agropulse.accounts.models import BuyerProfile
from core_agropulse.orders.models import Order, OrderItem
from core_agropulse.predictions.models import BuyerBehaviorPrediction, DemandForecast
from core_agropulse.produce.models import Produce


PERIOD_TO_DAYS = {
    "weekly": 7,
    "biweekly": 14,
    "monthly": 30,
    "seasonal": 90,
    "quarterly": 120,
}

ACTIVE_ORDER_STATUSES = ["PAID", "PROCESSING", "IN_TRANSIT", "COMPLETED"]


@dataclass
class BuyerReturnResult:
    prediction: BuyerBehaviorPrediction
    confidence: Decimal
    signals: dict


class PredictionEngineService:
    """Rule-based recommendation engine that uses existing marketplace history."""

    @staticmethod
    def _clamp(value: float, min_value: float, max_value: float) -> float:
        return max(min_value, min(max_value, value))

    @staticmethod
    def _normalize(value: float, min_value: float, max_value: float) -> float:
        if max_value == min_value:
            return 1.0
        return (value - min_value) / (max_value - min_value)

    @staticmethod
    def _resolve_forecast_period(forecast_period: str | None) -> str:
        if not forecast_period:
            return "weekly"
        return forecast_period if forecast_period in PERIOD_TO_DAYS else "weekly"

    @classmethod
    def generate_demand_forecast(
        cls, produce: Produce, forecast_period: str | None = None
    ) -> DemandForecast:
        period = cls._resolve_forecast_period(forecast_period)
        now = timezone.now()
        recent_window_start = now - timedelta(days=14)
        previous_window_start = now - timedelta(days=28)

        recent_qs = OrderItem.objects.filter(
            produce=produce,
            order__order_status__in=ACTIVE_ORDER_STATUSES,
            order__created_at__gte=recent_window_start,
        )
        previous_qs = OrderItem.objects.filter(
            produce=produce,
            order__order_status__in=ACTIVE_ORDER_STATUSES,
            order__created_at__gte=previous_window_start,
            order__created_at__lt=recent_window_start,
        )

        recent_quantity = recent_qs.aggregate(total=Sum("quantity"))["total"] or 0
        previous_quantity = previous_qs.aggregate(total=Sum("quantity"))["total"] or 0
        average_order_quantity = (
            recent_qs.aggregate(avg=Avg("quantity"))["avg"]
            or previous_qs.aggregate(avg=Avg("quantity"))["avg"]
            or 1
        )

        growth_ratio = 0.0
        if previous_quantity > 0:
            growth_ratio = (recent_quantity - previous_quantity) / previous_quantity
        elif recent_quantity > 0:
            growth_ratio = 1.0

        projected_days = PERIOD_TO_DAYS[period]
        recent_daily_avg = (
            recent_quantity / 14
            if recent_quantity
            else float(average_order_quantity) / 7
        )
        trend_boost = 1 + (0.35 * growth_ratio)
        trend_boost = cls._clamp(trend_boost, 0.75, 1.8)

        predicted_demand_volume = max(
            1,
            round(recent_daily_avg * projected_days * trend_boost),
        )
        demand_spike_probability = cls._clamp(50 + (growth_ratio * 35), 5, 95)
        recommended_stock_level = max(1, round(predicted_demand_volume * 1.2))

        return DemandForecast.objects.create(
            produce=produce,
            predicted_demand_volume=predicted_demand_volume,
            forecast_period=period,
            demand_spike_probability=Decimal(f"{demand_spike_probability:.2f}"),
            recommended_stock_level=recommended_stock_level,
        )

    @classmethod
    def generate_buyer_return_prediction(
        cls, buyer: BuyerProfile, produce: Produce
    ) -> BuyerReturnResult:
        now = timezone.now()
        purchase_history = (
            Order.objects.filter(
                buyer=buyer,
                order_status__in=ACTIVE_ORDER_STATUSES,
                items__produce=produce,
            )
            .distinct()
            .order_by("created_at")
        )

        order_dates = [order.created_at.date() for order in purchase_history]
        quantity_history = list(
            OrderItem.objects.filter(
                order__buyer=buyer,
                order__order_status__in=ACTIVE_ORDER_STATUSES,
                produce=produce,
            )
            .order_by("order__created_at")
            .values_list("quantity", flat=True)
        )

        if not order_dates:
            fallback_interval_days = 21
            predicted_return_date = (
                now + timedelta(days=fallback_interval_days)
            ).date()
            predicted_quantity = max(1, round(float(produce.quantity_available) * 0.05))
            return_probability = Decimal("28.00")
            confidence = Decimal("30.00")
            interval_stability = 0.0
        else:
            if len(order_dates) > 1:
                intervals = []
                for idx in range(1, len(order_dates)):
                    intervals.append((order_dates[idx] - order_dates[idx - 1]).days)
                avg_interval = max(1, round(mean(intervals)))
                interval_variance = (
                    mean([abs(i - avg_interval) for i in intervals]) / avg_interval
                )
                interval_stability = cls._clamp(1 - interval_variance, 0, 1)
            else:
                avg_interval = 14
                interval_stability = 0.35

            predicted_return_date = order_dates[-1] + timedelta(days=avg_interval)
            predicted_quantity = (
                max(1, round(mean(quantity_history))) if quantity_history else 1
            )

            days_since_last_purchase = (now.date() - order_dates[-1]).days
            recency_ratio = (
                days_since_last_purchase / avg_interval if avg_interval else 1.0
            )

            baseline = 62.0
            recency_alignment = max(0.0, 1 - abs(1 - recency_ratio))
            probability = (
                baseline + (recency_alignment * 25) + (interval_stability * 10)
            )
            return_probability = Decimal(f"{cls._clamp(probability, 5, 98):.2f}")
            confidence = Decimal(
                f"{cls._clamp((len(order_dates) * 15) + (interval_stability * 40), 25, 95):.2f}"
            )

        prediction = BuyerBehaviorPrediction.objects.create(
            buyer_id=buyer,
            produce_id=produce,
            predicted_return_date=predicted_return_date,
            predicted_quantity=predicted_quantity,
            return_probability=return_probability,
            buyer_category=buyer.buyer_type,
        )

        signals = {
            "historical_orders_count": len(order_dates),
            "avg_quantity": round(mean(quantity_history), 2) if quantity_history else 0,
            "interval_stability": round(interval_stability, 2),
        }

        return BuyerReturnResult(
            prediction=prediction, confidence=confidence, signals=signals
        )

    @classmethod
    def recommend_suppliers(
        cls,
        buyer: BuyerProfile,
        produce: Produce,
        quantity_required: int = 1,
        limit: int = 5,
    ) -> list[dict]:
        comparable_produces = Produce.objects.select_related(
            "farmer", "farmer__user"
        ).filter(
            Q(produce_name__iexact=produce.produce_name) | Q(category=produce.category),
            availability_status__in=["AVAILABLE", "LOW_STOCK"],
        )

        if not comparable_produces.exists():
            return []

        prices = [float(item.unit_price) for item in comparable_produces]
        qty_values = [item.quantity_available for item in comparable_produces]

        min_price = min(prices)
        max_price = max(prices)
        min_qty = min(qty_values)
        max_qty = max(qty_values)

        recommendations = []
        for candidate in comparable_produces:
            price_score = 1 - cls._normalize(
                float(candidate.unit_price), min_price, max_price
            )
            stock_score = cls._normalize(candidate.quantity_available, min_qty, max_qty)
            trust_raw = float(candidate.farmer.trust_score)
            trust_score = cls._clamp(trust_raw / 5, 0, 1)

            location_bonus = 0.1
            if buyer.location and candidate.farmer.farm_location:
                if (
                    buyer.location.strip().lower()
                    in candidate.farmer.farm_location.lower()
                ):
                    location_bonus = 0.2

            shortage_penalty = 0.0
            if candidate.quantity_available < quantity_required:
                shortage_penalty = 0.18

            confidence = (
                (price_score * 0.35)
                + (stock_score * 0.35)
                + (trust_score * 0.2)
                + location_bonus
                - shortage_penalty
            )
            confidence = cls._clamp(confidence, 0.05, 0.99)

            recommendations.append(
                {
                    "produce_id": str(candidate.id),
                    "produce_name": candidate.produce_name,
                    "supplier_id": str(candidate.farmer.id),
                    "supplier_name": candidate.farmer.farm_name,
                    "supplier_location": candidate.farmer.farm_location,
                    "unit_price": str(candidate.unit_price),
                    "quantity_available": candidate.quantity_available,
                    "availability_status": candidate.availability_status,
                    "trust_score": str(candidate.farmer.trust_score),
                    "match_confidence": round(confidence * 100, 2),
                    "recommended_for_quantity": candidate.quantity_available
                    >= quantity_required,
                    "reason": (
                        "Best overall balance of pricing, stock level, and supplier trust"
                        if confidence >= 0.75
                        else "Good fit with moderate confidence for this request"
                    ),
                }
            )

        recommendations.sort(key=lambda item: item["match_confidence"], reverse=True)
        return recommendations[:limit]
