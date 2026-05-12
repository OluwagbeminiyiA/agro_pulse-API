import uuid
from django.db import models
from core_agropulse.accounts.models import FarmerProfile


AVAILABILITY_STATUS_CHOICES = [
    ("AVAILABLE", "Available"),
    ("LOW_STOCK", "Low Stock"),
    ("SOLD_OUT", "Sold Out"),
]

PRODUCE_CATEGORY_CHOICES = [
    ("VEGETABLES", "Vegetables"),
    ("FRUITS", "Fruits"),
    ("GRAINS", "Grains"),
    ("DAIRY", "Dairy"),
    ("MEAT", "Meat"),
    ("OTHER", "Other"),
]


class Produce(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    farmer = models.ForeignKey(
        FarmerProfile, on_delete=models.CASCADE, related_name="produces"
    )
    produce_name = models.CharField(max_length=255)
    category = models.CharField(max_length=50, choices=PRODUCE_CATEGORY_CHOICES)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_available = models.IntegerField()
    harvest_date = models.DateField()
    availability_status = models.CharField(
        max_length=20, choices=AVAILABILITY_STATUS_CHOICES, default="AVAILABLE"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["farmer", "-created_at"]),
            models.Index(fields=["availability_status"]),
            models.Index(fields=["category"]),
        ]

    def __str__(self):
        return f"{self.produce_name} - {self.farmer.farm_name} ({self.availability_status})"
