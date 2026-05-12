from django.contrib import admin
from core_agropulse.payments.models import (
    Payment,
    EscrowAccount,
    PaymentSplit,
    Payout,
    VirtualAccount,
    VirtualAccountTransaction,
)


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


@admin.register(VirtualAccount)
class VirtualAccountAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "virtual_account_number",
        "account_name",
        "bank_name",
        "is_active",
        "created_at",
    )
    list_filter = ("is_active", "bank_name", "created_at")
    search_fields = (
        "virtual_account_number",
        "account_name",
        "email",
        "farmer__user__full_name",
        "transporter__user__full_name",
    )
    readonly_fields = ("id", "created_at", "updated_at")
    fieldsets = (
        (
            "Account Information",
            {"fields": ("id", "virtual_account_number", "bank_name")},
        ),
        ("Owner", {"fields": ("farmer", "transporter")}),
        (
            "Account Holder Details",
            {
                "fields": (
                    "account_name",
                    "first_name",
                    "last_name",
                    "email",
                    "mobile_num",
                    "bvn",
                )
            },
        ),
        ("Status", {"fields": ("is_active",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )


@admin.register(VirtualAccountTransaction)
class VirtualAccountTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "transaction_reference",
        "virtual_account",
        "pricipal_amount",
        "settled_amount",
        "webhook_processed",
        "created_at",
    )
    list_filter = ("webhook_processed", "transaction_date", "currency", "created_at")
    search_fields = (
        "transaction_reference",
        "virtual_account__virtual_account_number",
        "sender",
    )
    readonly_fields = ("id", "created_at")
    fieldsets = (
        (
            "Transaction Information",
            {
                "fields": (
                    "id",
                    "transaction_reference",
                    "virtual_account",
                    "sender",
                )
            },
        ),
        (
            "Amounts",
            {"fields": ("pricipal_amount", "settled_amount", "fee", "currency")},
        ),
        ("Details", {"fields": ("remarks", "transaction_date")}),
        ("Webhook", {"fields": ("webhook_processed", "webhook_payload")}),
        ("Timestamp", {"fields": ("created_at",)}),
    )
