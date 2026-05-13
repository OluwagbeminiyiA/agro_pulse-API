from django.contrib import admin
from core_agropulse.subscriptions.models import (
    Subscription,
    SubscriptionOrder,
    SubscriptionPayment,
)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "buyer",
        "farmer",
        "produce",
        "frequency",
        "status",
        "next_expected_order_date",
        "active",
        "created_at",
    )
    list_filter = ("status", "frequency", "active", "created_at")
    search_fields = (
        "buyer__user__full_name",
        "farmer__user__full_name",
        "produce__produce_name",
    )
    readonly_fields = ("id", "created_at", "updated_at", "subscription_start_date")
    fieldsets = (
        (
            "Subscription Information",
            {"fields": ("id", "buyer", "farmer", "produce", "frequency")},
        ),
        (
            "Order Details",
            {"fields": ("expected_quantity", "next_expected_order_date")},
        ),
        ("Status", {"fields": ("status", "active", "subscription_end_date")}),
        ("Dates", {"fields": ("subscription_start_date", "created_at", "updated_at")}),
    )


@admin.register(SubscriptionOrder)
class SubscriptionOrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "subscription",
        "quantity",
        "total_amount",
        "order_status",
        "scheduled_date",
        "created_at",
    )
    list_filter = ("order_status", "scheduled_date", "created_at")
    search_fields = (
        "subscription__buyer__user__full_name",
        "subscription__farmer__user__full_name",
    )
    readonly_fields = ("id", "created_at", "updated_at", "total_amount")
    fieldsets = (
        (
            "Subscription Order Information",
            {"fields": ("id", "subscription", "order_id")},
        ),
        ("Order Details", {"fields": ("quantity", "unit_price", "total_amount")}),
        ("Status", {"fields": ("order_status", "scheduled_date")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )


@admin.register(SubscriptionPayment)
class SubscriptionPaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "subscription_order",
        "amount",
        "payment_status",
        "payment_method",
        "payment_date",
        "created_at",
    )
    list_filter = ("payment_status", "payment_method", "payment_date", "created_at")
    search_fields = ("subscription_order__id",)
    readonly_fields = ("id", "created_at", "updated_at", "payment_date")
    fieldsets = (
        ("Payment Information", {"fields": ("id", "subscription_order", "amount")}),
        ("Status", {"fields": ("payment_status", "payment_method", "payment_date")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )
