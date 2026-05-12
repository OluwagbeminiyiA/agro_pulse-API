import uuid
from django.db import models
from core_agropulse.accounts.models import BuyerProfile, FarmerProfile
from core_agropulse.produce.models import Produce


ORDER_STATUS_CHOICES = [
    ("PENDING", "Pending"),
    ("PAID", "Paid"),
    ("PROCESSING", "Processing"),
    ("IN_TRANSIT", "In Transit"),
    ("COMPLETED", "Completed"),
    ("CANCELLED", "Cancelled"),
]

DELIVERY_TYPE_CHOICES = [
    ("PICKUP", "Pickup"),
    ("DELIVERY", "Delivery"),
]


class Order(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    buyer = models.ForeignKey(
        BuyerProfile, on_delete=models.CASCADE, related_name="orders"
    )
    farmer = models.ForeignKey(
        FarmerProfile, on_delete=models.CASCADE, related_name="orders"
    )
    total = models.DecimalField(max_digits=10, decimal_places=2)
    order_status = models.CharField(
        max_length=20, choices=ORDER_STATUS_CHOICES, default="PENDING"
    )
    delivery_type = models.CharField(max_length=20, choices=DELIVERY_TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["buyer", "-created_at"]),
            models.Index(fields=["farmer", "-created_at"]),
            models.Index(fields=["order_status"]),
        ]

    def __str__(self):
        return f"Order {self.id} - {self.buyer.business_name} from {self.farmer.farm_name} ({self.order_status})"


class OrderItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    produce = models.ForeignKey(
        Produce, on_delete=models.CASCADE, related_name="order_items"
    )
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["order", "-created_at"]),
            models.Index(fields=["produce"]),
        ]

    def save(self, *args, **kwargs):
        """Auto-calculate subtotal on save"""
        self.subtotal = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.produce.produce_name} x {self.quantity} - Order {self.order.id}"
