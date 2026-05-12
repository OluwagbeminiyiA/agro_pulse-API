from rest_framework import serializers
from core_agropulse.orders.models import Order, OrderItem


class OrderSerializer(serializers.ModelSerializer):
    buyer_business_name = serializers.CharField(
        source="buyer.business_name", read_only=True
    )
    buyer_email = serializers.CharField(source="buyer.user.email", read_only=True)
    farmer_farm_name = serializers.CharField(source="farmer.farm_name", read_only=True)
    farmer_user_email = serializers.CharField(
        source="farmer.user.email", read_only=True
    )

    class Meta:
        model = Order
        fields = [
            "id",
            "buyer",
            "buyer_business_name",
            "buyer_email",
            "farmer",
            "farmer_farm_name",
            "farmer_user_email",
            "total",
            "order_status",
            "delivery_type",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class OrderDetailSerializer(serializers.ModelSerializer):
    buyer_details = serializers.SerializerMethodField(read_only=True)
    farmer_details = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "buyer",
            "buyer_details",
            "farmer",
            "farmer_details",
            "total",
            "order_status",
            "delivery_type",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_buyer_details(self, obj):
        return {
            "business_name": obj.buyer.business_name,
            "buyer_type": obj.buyer.buyer_type,
            "location": obj.buyer.location,
            "buyer_email": obj.buyer.user.email,
            "buyer_phone": obj.buyer.user.phone_number,
        }

    def get_farmer_details(self, obj):
        return {
            "farm_name": obj.farmer.farm_name,
            "farm_location": obj.farmer.farm_location,
            "farmer_name": obj.farmer.user.full_name,
            "farmer_email": obj.farmer.user.email,
            "farmer_phone": obj.farmer.user.phone_number,
        }


class OrderItemSerializer(serializers.ModelSerializer):
    produce_name = serializers.CharField(source="produce.produce_name", read_only=True)
    produce_category = serializers.CharField(source="produce.category", read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "order",
            "produce",
            "produce_name",
            "produce_category",
            "quantity",
            "unit_price",
            "subtotal",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "subtotal", "created_at", "updated_at"]


class OrderDetailWithItemsSerializer(serializers.ModelSerializer):
    buyer_details = serializers.SerializerMethodField(read_only=True)
    farmer_details = serializers.SerializerMethodField(read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "buyer",
            "buyer_details",
            "farmer",
            "farmer_details",
            "items",
            "total",
            "order_status",
            "delivery_type",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_buyer_details(self, obj):
        return {
            "business_name": obj.buyer.business_name,
            "buyer_type": obj.buyer.buyer_type,
            "location": obj.buyer.location,
            "buyer_email": obj.buyer.user.email,
            "buyer_phone": obj.buyer.user.phone_number,
        }

    def get_farmer_details(self, obj):
        return {
            "farm_name": obj.farmer.farm_name,
            "farm_location": obj.farmer.farm_location,
            "farmer_name": obj.farmer.user.full_name,
            "farmer_email": obj.farmer.user.email,
            "farmer_phone": obj.farmer.user.phone_number,
        }
