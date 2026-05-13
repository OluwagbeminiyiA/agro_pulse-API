import uuid
from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("accounts", "0003_rename_full_user_full_name"),
        ("produce", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="BuyerBehaviorPrediction",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("predicted_return_date", models.DateField()),
                ("predicted_quantity", models.IntegerField()),
                (
                    "return_probability",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=5,
                        validators=[
                            MinValueValidator(Decimal("0")),
                            MaxValueValidator(Decimal("100")),
                        ],
                    ),
                ),
                (
                    "buyer_category",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("generated_at", models.DateTimeField(auto_now=True)),
                (
                    "buyer_id",
                    models.ForeignKey(
                        db_index=True,
                        on_delete=models.deletion.CASCADE,
                        related_name="buyer_behaviour",
                        to="accounts.buyerprofile",
                    ),
                ),
                (
                    "produce_id",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE, to="produce.produce"
                    ),
                ),
            ],
            options={
                "ordering": ["-generated_at"],
                "verbose_name": "Buyer Behavior Prediction",
                "verbose_name_plural": "Buyer Behavior Predictions",
            },
        ),
        migrations.CreateModel(
            name="DemandForecast",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("predicted_demand_volume", models.IntegerField()),
                (
                    "forecast_period",
                    models.CharField(
                        choices=[
                            ("weekly", "Weekly"),
                            ("biweekly", "Bi-weekly"),
                            ("monthly", "Monthly"),
                            ("seasonal", "Seasonal"),
                            ("quarterly", "Quarterly"),
                        ],
                        default="weekly",
                        max_length=20,
                    ),
                ),
                (
                    "demand_spike_probability",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=5,
                        validators=[
                            MinValueValidator(Decimal("0")),
                            MaxValueValidator(Decimal("100")),
                        ],
                    ),
                ),
                ("recommended_stock_level", models.IntegerField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("generated_at", models.DateTimeField(auto_now=True)),
                (
                    "produce",
                    models.ForeignKey(
                        db_index=True,
                        on_delete=models.deletion.CASCADE,
                        related_name="demand_forecast",
                        to="produce.produce",
                    ),
                ),
            ],
            options={
                "ordering": ["-generated_at"],
                "verbose_name": "Demand Forecast",
                "verbose_name_plural": "Demand Forecasts",
            },
        ),
        migrations.AddIndex(
            model_name="buyerbehaviorprediction",
            index=models.Index(
                fields=["buyer_id", "-generated_at"],
                name="predictions_b_buyer_i_2f0c13_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="demandforecast",
            index=models.Index(
                fields=["produce", "-generated_at"],
                name="predictions_d_produce_8bbdcb_idx",
            ),
        ),
    ]
