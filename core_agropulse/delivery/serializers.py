from rest_framework import serializers
from core_agropulse.delivery.models import Delivery, RiderEarnings


class DeliverySerializer(serializers.ModelSerializer):
    transporter_name = serializers.CharField(
        source="transporter.user.full_name", read_only=True
    )
    transporter_vehicle = serializers.CharField(
        source="transporter.vehicle_type", read_only=True
    )
    order_total = serializers.DecimalField(
        source="order.total", read_only=True, max_digits=10, decimal_places=2
    )
    buyer_name = serializers.CharField(
        source="order.buyer.user.full_name", read_only=True
    )
    farmer_name = serializers.CharField(
        source="order.farmer.user.full_name", read_only=True
    )

    class Meta:
        model = Delivery
        fields = [
            "id",
            "order",
            "transporter",
            "transporter_name",
            "transporter_vehicle",
            "delivery_status",
            "delivery_address",
            "buyer_name",
            "farmer_name",
            "order_total",
            "picked_up_at",
            "delivered_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "delivered_at"]


class DeliveryDetailSerializer(serializers.ModelSerializer):
    transporter_details = serializers.SerializerMethodField(read_only=True)
    order_details = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Delivery
        fields = [
            "id",
            "order",
            "order_details",
            "transporter",
            "transporter_details",
            "delivery_status",
            "delivery_address",
            "picked_up_at",
            "delivered_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_transporter_details(self, obj):
        if obj.transporter:
            return {
                "id": str(obj.transporter.id),
                "name": obj.transporter.user.full_name,
                "email": obj.transporter.user.email,
                "phone": obj.transporter.user.phone_number,
                "vehicle_type": obj.transporter.vehicle_type,
                "plate_number": obj.transporter.plate_number,
                "service_area": obj.transporter.service_area,
            }
        return None

    def get_order_details(self, obj):
        return {
            "id": str(obj.order.id),
            "buyer_name": obj.order.buyer.user.full_name,
            "farmer_name": obj.order.farmer.user.full_name,
            "total": str(obj.order.total),
            "order_status": obj.order.order_status,
            "delivery_type": obj.order.delivery_type,
        }


class RiderEarningsSerializer(serializers.ModelSerializer):
    transporter_name = serializers.CharField(
        source="transporter.user.full_name", read_only=True
    )
    delivery_order_id = serializers.CharField(
        source="delivery.order.id", read_only=True
    )
    delivery_address = serializers.CharField(
        source="delivery.delivery_address", read_only=True
    )

    class Meta:
        model = RiderEarnings
        fields = [
            "id",
            "transporter",
            "transporter_name",
            "delivery",
            "delivery_order_id",
            "delivery_address",
            "earnings_amount",
            "payment_status",
            "paid_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class RiderEarningsDetailSerializer(serializers.ModelSerializer):
    transporter_details = serializers.SerializerMethodField(read_only=True)
    delivery_details = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = RiderEarnings
        fields = [
            "id",
            "transporter",
            "transporter_details",
            "delivery",
            "delivery_details",
            "earnings_amount",
            "payment_status",
            "paid_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_transporter_details(self, obj):
        return {
            "id": str(obj.transporter.id),
            "name": obj.transporter.user.full_name,
            "email": obj.transporter.user.email,
            "phone": obj.transporter.user.phone_number,
            "vehicle_type": obj.transporter.vehicle_type,
        }

    def get_delivery_details(self, obj):
        return {
            "id": str(obj.delivery.id),
            "order_id": str(obj.delivery.order.id),
            "delivery_address": obj.delivery.delivery_address,
            "delivery_status": obj.delivery.delivery_status,
            "delivered_at": obj.delivery.delivered_at,
        }
