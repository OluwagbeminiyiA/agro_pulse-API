import uuid

from cfgv import ValidationError
from django.db import models
from decimal import Decimal

from core_agropulse.orders.models import Order
from core_agropulse.accounts.models import (
    FarmerProfile,
    BuyerProfile,
    TransporterProfile,
)

PAYMENT_STATUS_CHOICES = [
    ("PENDING", "Pending"),
    ("SUCCESS", "Success"),
    ("FAILED", "Failed"),
    ("REFUNDED", "Refunded"),
]

PAYOUT_STATUS_CHOICES = [
    ("PENDING", "Pending"),
    ("PROCESSING", "Processing"),
    ("COMPLETED", "Completed"),
    ("FAILED", "Failed"),
]

CURRENCY_CHOICES = [("USD", "usd"), ("NGN", "ngn")]

CHANNEL_CHOICES = [
    ("USSD", "ussd"),
    ("CARD", "card"),
    ("TRANSFER", "Transfer"),
    ("VIRTUAL-ACCOUNT", "virtual-account"),
]


class Payment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    buyer = models.ForeignKey(
        BuyerProfile, on_delete=models.CASCADE, related_name="payments"
    )
    order = models.OneToOneField(
        Order, on_delete=models.CASCADE, related_name="payment"
    )
    email = models.EmailField()
    squad_transaction_id = models.CharField(max_length=255, null=True, blank=True)
    payment_method = models.CharField(max_length=100, default="card")
    payment_status = models.CharField(
        max_length=20, choices=PAYMENT_STATUS_CHOICES, default="PENDING"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default="NGN")

    channel = models.CharField(
        max_length=30, choices=CHANNEL_CHOICES, null=True, blank=True
    )
    gateway_response = models.TextField(blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)
    checkout_url = models.URLField(null=True, blank=True)

    webhook_recieved = models.BooleanField(default=False)
    webhook_verified = models.BooleanField(default=False)
    webhook_payload = models.JSONField(default=dict, blank=True)

    escrow_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["payment_status", "-created_at"]),
            models.Index(fields=["order"]),
            models.Index(fields=["squad_transaction_id"]),
        ]

    def __str__(self):
        return f"Payment {self.id} - Order {self.order.id} ({self.payment_status})"

    @property
    def amount_in_kobo(self):
        """Convert the naira amount to kobo # We would speak about this later becauseeeee"""
        return int(float(self.amount) * 100)


class VirtualAccount(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4(), editable=False)
    transporter = models.OneToOneField(
        TransporterProfile, on_delete=models.CASCADE, related_name="virtual_account"
    )
    farmer = models.OneToOneField(
        FarmerProfile, on_delete=models.CASCADE, related_name="virtual_account"
    )
    virtual_account_number = models.CharField(max_length=20, unique=True)
    bank_name = models.CharField(max_length=100)
    account_name = models.CharField(max_length=255)

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    mobile_num = models.CharField(max_length=14)
    bvn = models.CharField(max_length=11)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def clean(self):
        if self.farmer and self.transporter:
            raise ValidationError(
                "An account cannot belong to both a farmer and a transporter"
            )
        if not self.farmer and not self.transporter:
            raise ValidationError(
                "An account must belong to either a farmer or a transporter"
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def owner(self):
        return self.farmer or self.transporter

    def __str__(self):
        return f"Account {self.virtual_account_number} - {self.owner}"


class VirtualAccountTransaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4(), editable=False)
    virtual_account = models.ForeignKey(
        VirtualAccount, on_delete=models.CASCADE, related_name="transactions"
    )
    transaction_reference = models.CharField(max_length=255, unique=True, db_index=True)
    pricipal_amount = models.DecimalField(max_digits=12, decimal_places=2)
    settled_amount = models.DecimalField(max_digits=12, decimal_places=2)
    fee = models.DecimalField(max_digits=12, decimal_places=2)
    sender = models.CharField(max_length=255)
    remarks = models.TextField()
    currency = models.CharField(max_length=3, default="NGN")
    transaction_date = models.DateTimeField()

    webhook_processed = models.BooleanField(default=False)
    webhook_payload = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-transaction_date"]
        indexes = [
            models.Index(fields=["transaction_reference"]),
            models.Index(fields=["virtual_account", "-transaction_date"]),
        ]

    def __str__(self):
        return f"{self.transaction_reference} - {self.pricipal_amount}"


class EscrowAccount(models.Model):
    """Escrow account holds funds until delivery is confirmed"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.OneToOneField(
        Payment, on_delete=models.CASCADE, related_name="escrow"
    )
    farmer = models.ForeignKey(
        FarmerProfile, on_delete=models.CASCADE, related_name="escrow_accounts"
    )
    amount_held = models.DecimalField(max_digits=10, decimal_places=2)
    release_status = models.CharField(
        max_length=20,
        choices=[
            ("HELD", "Held"),
            ("RELEASED", "Released"),
            ("DISPUTED", "Disputed"),
        ],
        default="HELD",
    )
    released_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["farmer", "-created_at"]),
            models.Index(fields=["release_status"]),
        ]

    def __str__(self):
        return f"Escrow {self.id} - {self.farmer.farm_name} (${self.amount_held})"


class PaymentSplit(models.Model):
    """Tracks payment split between farmer, rider, and platform"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.OneToOneField(
        Payment, on_delete=models.CASCADE, related_name="split"
    )
    farmer_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    rider_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    platform_fee = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    farmer_processed = models.BooleanField(default=False)
    rider_processed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Split {self.id} - Farmer: ₦{self.farmer_amount}, Rider: ₦{self.rider_amount}"


class Payout(models.Model):
    """Tracks payouts to farmers and riders"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.ForeignKey(
        Payment, on_delete=models.CASCADE, related_name="payouts"
    )
    farmer = models.ForeignKey(
        FarmerProfile,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="payouts",
    )
    rider = models.ForeignKey(
        TransporterProfile,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="payouts",
    )
    payout_type = models.CharField(
        max_length=20, choices=[("FARMER", "Farmer"), ("RIDER", "Rider")]
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payout_status = models.CharField(
        max_length=20, choices=PAYOUT_STATUS_CHOICES, default="PENDING"
    )
    bank_reference = models.CharField(max_length=255, null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["payout_status", "-created_at"]),
            models.Index(fields=["farmer"]),
            models.Index(fields=["rider"]),
        ]

    def __str__(self):
        recipient = self.farmer or self.rider
        return f"Payout {self.id} - {recipient} (${self.amount})"
