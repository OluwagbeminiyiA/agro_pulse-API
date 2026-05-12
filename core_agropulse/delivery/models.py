import uuid
from django.db import models
from decimal import Decimal
from core_agropulse.accounts.models import TransporterProfile
from core_agropulse.orders.models import Order


DELIVERY_STATUS_CHOICES = [
    ("PENDING", "Pending"),
    ("PICKED_UP", "Picked Up"),
    ("IN_TRANSIT", "In Transit"),
    ("DELIVERED", "Delivered"),
]


class Delivery(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.OneToOneField(
        Order, on_delete=models.CASCADE, related_name="delivery"
    )
    transporter = models.ForeignKey(
        TransporterProfile,
        on_delete=models.SET_NULL,
        null=True,
        related_name="deliveries",
    )
    delivery_status = models.CharField(
        max_length=20, choices=DELIVERY_STATUS_CHOICES, default="PENDING"
    )
    delivery_address = models.TextField()
    picked_up_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["delivery_status", "-created_at"]),
            models.Index(fields=["transporter", "-created_at"]),
            models.Index(fields=["order"]),
        ]

    def __str__(self):
        return f"Delivery {self.id} - Order {self.order.id} ({self.delivery_status})"


class RiderEarnings(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transporter = models.ForeignKey(
        TransporterProfile, on_delete=models.CASCADE, related_name="earnings"
    )
    delivery = models.OneToOneField(
        Delivery, on_delete=models.CASCADE, related_name="earnings"
    )
    earnings_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    payment_status = models.CharField(
        max_length=20,
        choices=[
            ("PENDING", "Pending"),
            ("PAID", "Paid"),
            ("CANCELLED", "Cancelled"),
        ],
        default="PENDING",
    )
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["transporter", "-created_at"]),
            models.Index(fields=["payment_status"]),
        ]

    def __str__(self):
        return f"Earnings {self.id} - {self.transporter.user.full_name} - ₦{self.earnings_amount}"
