import uuid
from decimal import Decimal

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from core_agropulse.accounts.models import BuyerProfile
from core_agropulse.produce.models import Produce


FORECAST_PERIOD_CHOICES = [
    ("weekly", "Weekly"),
    ("biweekly", "Bi-weekly"),
    ("monthly", "Monthly"),
    ("seasonal", "Seasonal"),
    ("quarterly", "Quarterly"),
]


# Create your models here.
class BuyerBehaviorPrediction(models.Model):
    """Predicts buyer behavior including return dates, quantities, and probabilities."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    buyer_id = models.ForeignKey(
        BuyerProfile,
        on_delete=models.CASCADE,
        related_name="buyer_behaviour",
        db_index=True,
    )
    produce_id = models.ForeignKey(Produce, on_delete=models.CASCADE)
    predicted_return_date = models.DateField()
    predicted_quantity = models.IntegerField()
    return_probability = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("100"))],
    )
    buyer_category = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    generated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-generated_at"]
        indexes = [models.Index(fields=["buyer_id", "-generated_at"])]
        verbose_name = "Buyer Behavior Prediction"
        verbose_name_plural = "Buyer Behavior Predictions"

    def __str__(self):
        return f"Buyer {self.buyer_id} is set to return {self.predicted_return_date}"


class DemandForecast(models.Model):
    """Forecasts demand for produce including volume spikes and stock recommendations."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    produce = models.ForeignKey(
        Produce, on_delete=models.CASCADE, related_name="demand_forecast", db_index=True
    )
    predicted_demand_volume = models.IntegerField()
    forecast_period = models.CharField(
        max_length=20, choices=FORECAST_PERIOD_CHOICES, default="weekly"
    )
    demand_spike_probability = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("100"))],
    )
    recommended_stock_level = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    generated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-generated_at"]
        indexes = [models.Index(fields=["produce", "-generated_at"])]
        verbose_name = "Demand Forecast"
        verbose_name_plural = "Demand Forecasts"

    def __str__(self):
        return f"produce {self.produce} demand is expected to have {self.predicted_demand_volume} soon"
