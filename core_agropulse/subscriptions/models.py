import uuid
from django.db import models
from django.utils import timezone
from datetime import timedelta

from core_agropulse.accounts.models import BuyerProfile, FarmerProfile
from core_agropulse.produce.models import Produce


FREQUENCY_CHOICES = [
    ("DAILY", "Daily"),
    ("WEEKLY", "Weekly"),
    ("MONTHLY", "Monthly"),
]

SUBSCRIPTION_STATUS_CHOICES = [
    ("ACTIVE", "Active"),
    ("PAUSED", "Paused"),
    ("CANCELLED", "Cancelled"),
]


class Subscription(models.Model):
    """Recurring product subscription for buyers"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    buyer = models.ForeignKey(
        BuyerProfile, on_delete=models.CASCADE, related_name="subscriptions"
    )
    farmer = models.ForeignKey(
        FarmerProfile, on_delete=models.CASCADE, related_name="subscriptions"
    )
    produce = models.ForeignKey(
        Produce, on_delete=models.CASCADE, related_name="subscriptions"
    )
    frequency = models.CharField(
        max_length=20, choices=FREQUENCY_CHOICES, default="WEEKLY"
    )
    expected_quantity = models.IntegerField(default=1)
    next_expected_order_date = models.DateField()
    active = models.BooleanField(default=True)
    status = models.CharField(
        max_length=20, choices=SUBSCRIPTION_STATUS_CHOICES, default="ACTIVE"
    )
    subscription_start_date = models.DateField(auto_now_add=True)
    subscription_end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["buyer", "-created_at"]),
            models.Index(fields=["farmer", "-created_at"]),
            models.Index(fields=["active", "next_expected_order_date"]),
            models.Index(fields=["status"]),
        ]
        unique_together = ["buyer", "farmer", "produce"]

    def __str__(self):
        return (
            f"Subscription {self.id} - {self.buyer.user.full_name} ({self.frequency})"
        )

    def calculate_next_order_date(self):
        """Calculate next order date based on frequency"""
        if self.frequency == "DAILY":
            return self.next_expected_order_date + timedelta(days=1)
        elif self.frequency == "WEEKLY":
            return self.next_expected_order_date + timedelta(weeks=1)
        elif self.frequency == "MONTHLY":
            return self.next_expected_order_date + timedelta(days=30)
        return self.next_expected_order_date

    def pause(self):
        """Pause the subscription"""
        self.status = "PAUSED"
        self.active = False
        self.save()

    def resume(self):
        """Resume a paused subscription"""
        self.status = "ACTIVE"
        self.active = True
        self.save()

    def cancel(self):
        """Cancel the subscription"""
        self.status = "CANCELLED"
        self.active = False
        self.subscription_end_date = timezone.now().date()
        self.save()


class SubscriptionOrder(models.Model):
    """Auto-generated orders from subscriptions"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subscription = models.ForeignKey(
        Subscription, on_delete=models.CASCADE, related_name="orders"
    )
    order_id = models.UUIDField(null=True, blank=True)  # Link to Order model if created
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    order_status = models.CharField(
        max_length=20,
        choices=[
            ("PENDING", "Pending"),
            ("CONFIRMED", "Confirmed"),
            ("DELIVERED", "Delivered"),
            ("FAILED", "Failed"),
            ("SKIPPED", "Skipped"),
        ],
        default="PENDING",
    )
    scheduled_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-scheduled_date"]
        indexes = [
            models.Index(fields=["subscription", "-scheduled_date"]),
            models.Index(fields=["order_status", "-created_at"]),
        ]

    def __str__(self):
        return f"SubscriptionOrder {self.id} - {self.order_status}"


class SubscriptionPayment(models.Model):
    """Track payments for subscription orders"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subscription_order = models.OneToOneField(
        SubscriptionOrder, on_delete=models.CASCADE, related_name="payment"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(
        max_length=20,
        choices=[
            ("PENDING", "Pending"),
            ("COMPLETED", "Completed"),
            ("FAILED", "Failed"),
            ("REFUNDED", "Refunded"),
        ],
        default="PENDING",
    )
    payment_method = models.CharField(max_length=100, default="auto")
    payment_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["payment_status", "-created_at"]),
        ]

    def __str__(self):
        return f"SubscriptionPayment {self.id} - {self.payment_status}"
