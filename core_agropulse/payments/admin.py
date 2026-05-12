from django.contrib import admin
from core_agropulse.payments.models import Payment, EscrowAccount, PaymentSplit, Payout


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "payment_status",
        "amount",
        "squad_transaction_id",
        "escrow_enabled",
        "created_at",
    )
    list_filter = ("payment_status", "created_at", "escrow_enabled")
    search_fields = ("order__id", "squad_transaction_id")
    readonly_fields = ("id", "created_at", "updated_at")
    fieldsets = (
        ("Payment Information", {"fields": ("id", "order", "amount")}),
        (
            "Squad Details",
            {"fields": ("squad_transaction_id", "payment_method", "payment_status")},
        ),
        ("Escrow", {"fields": ("escrow_enabled",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )


@admin.register(EscrowAccount)
class EscrowAccountAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "payment",
        "farmer",
        "amount_held",
        "release_status",
        "created_at",
    )
    list_filter = ("release_status", "created_at")
    search_fields = ("payment__id", "farmer__user__full_name", "farmer__farm_name")
    readonly_fields = ("id", "created_at", "updated_at")
    fieldsets = (
        ("Escrow Information", {"fields": ("id", "payment", "farmer", "amount_held")}),
        ("Status", {"fields": ("release_status", "released_at")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )


@admin.register(PaymentSplit)
class PaymentSplitAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "payment",
        "farmer_amount",
        "rider_amount",
        "platform_fee",
        "created_at",
    )
    list_filter = ("created_at",)
    search_fields = ("payment__id",)
    readonly_fields = ("id", "created_at", "updated_at")
    fieldsets = (
        ("Payment Split", {"fields": ("id", "payment")}),
        (
            "Split Amounts",
            {"fields": ("farmer_amount", "rider_amount", "platform_fee")},
        ),
        ("Processing Status", {"fields": ("farmer_processed", "rider_processed")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )


@admin.register(Payout)
class PayoutAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "payment",
        "payout_type",
        "amount",
        "payout_status",
        "completed_at",
        "created_at",
    )
    list_filter = ("payout_status", "payout_type", "created_at")
    search_fields = (
        "payment__id",
        "farmer__user__full_name",
        "rider__user__full_name",
        "bank_reference",
    )
    readonly_fields = ("id", "created_at", "updated_at")
    fieldsets = (
        ("Payout Information", {"fields": ("id", "payment", "payout_type", "amount")}),
        ("Recipient", {"fields": ("farmer", "rider")}),
        ("Status", {"fields": ("payout_status", "completed_at", "bank_reference")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )
