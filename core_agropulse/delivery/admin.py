from django.contrib import admin
from core_agropulse.delivery.models import Delivery, RiderEarnings


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "transporter",
        "delivery_status",
        "created_at",
        "delivered_at",
    )
    list_filter = ("delivery_status", "created_at", "transporter")
    search_fields = ("order__id", "delivery_address", "transporter__user__full_name")
    readonly_fields = ("id", "created_at", "updated_at", "picked_up_at", "delivered_at")
    fieldsets = (
        (
            "Delivery Information",
            {"fields": ("id", "order", "transporter", "delivery_address")},
        ),
        ("Status", {"fields": ("delivery_status", "picked_up_at", "delivered_at")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )


@admin.register(RiderEarnings)
class RiderEarningsAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "transporter",
        "delivery",
        "earnings_amount",
        "payment_status",
        "created_at",
    )
    list_filter = ("payment_status", "created_at", "transporter")
    search_fields = ("transporter__user__full_name", "delivery__order__id")
    readonly_fields = ("id", "created_at", "updated_at")
    fieldsets = (
        (
            "Earnings Information",
            {"fields": ("id", "transporter", "delivery", "earnings_amount")},
        ),
        ("Payment", {"fields": ("payment_status", "paid_at")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )
