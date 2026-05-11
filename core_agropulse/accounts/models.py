import uuid
from django.contrib.auth.models import PermissionsMixin, AbstractBaseUser
from django.db import models

from core_agropulse.accounts.managers import CustomUserManager

ROLE_CHOICES = [
    ("BUYER", "Buyer"),
    ("SELLER", "Seller"),
    ("TRANSPORTER", "Transporter"),
]

BUYER_TYPE_CHOICES = [
    ("INDIVIDUAL", "Individual"),
    ("RESTAURANT", "Restaurant"),
    ("WHOLESALER", "Wholesaler"),
]


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.full_name} ({self.role})"


class FarmerProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="farmer_profile"
    )
    farm_name = models.CharField(max_length=255)
    farm_location = models.CharField(max_length=255)
    trust_score = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.farm_name} - {self.user.full_name}"


class BuyerProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="buyer_profile"
    )
    business_name = models.CharField(max_length=255, null=True, blank=True)
    buyer_type = models.CharField(max_length=20, choices=BUYER_TYPE_CHOICES)
    location = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.business_name} ({self.buyer_type})"


class TransporterProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="transporter_profile"
    )
    vehicle_type = models.CharField(max_length=255)
    plate_number = models.CharField(max_length=50)
    service_area = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.plate_number} - {self.user.full_name}"
