from rest_framework import serializers
from core_agropulse.subscriptions.models import (
    Subscription,
    SubscriptionOrder,
    SubscriptionPayment,
)


class SubscriptionSerializer(serializers.ModelSerializer):
    buyer_name = serializers.CharField(source="buyer.user.full_name", read_only=True)
    farmer_name = serializers.CharField(source="farmer.user.full_name", read_only=True)
    produce_name = serializers.CharField(source="produce.produce_name", read_only=True)
    produce_price = serializers.DecimalField(
        source="produce.unit_price", read_only=True, max_digits=10, decimal_places=2
    )

    class Meta:
        model = Subscription
        fields = [
            "id",
            "buyer",
            "buyer_name",
            "farmer",
            "farmer_name",
            "produce",
            "produce_name",
            "produce_price",
            "frequency",
            "expected_quantity",
            "next_expected_order_date",
            "active",
            "status",
            "subscription_start_date",
            "subscription_end_date",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "subscription_start_date",
            "subscription_end_date",
        ]


class SubscriptionDetailSerializer(serializers.ModelSerializer):
    buyer_details = serializers.SerializerMethodField(read_only=True)
    farmer_details = serializers.SerializerMethodField(read_only=True)
    produce_details = serializers.SerializerMethodField(read_only=True)
    orders = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Subscription
        fields = [
            "id",
            "buyer",
            "buyer_details",
            "farmer",
            "farmer_details",
            "produce",
            "produce_details",
            "frequency",
            "expected_quantity",
            "next_expected_order_date",
            "active",
            "status",
            "subscription_start_date",
            "subscription_end_date",
            "orders",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "subscription_start_date",
            "subscription_end_date",
        ]

    def get_buyer_details(self, obj):
        return {
            "id": str(obj.buyer.id),
            "name": obj.buyer.user.full_name,
            "email": obj.buyer.user.email,
            "business_name": obj.buyer.business_name,
        }

    def get_farmer_details(self, obj):
        return {
            "id": str(obj.farmer.id),
            "name": obj.farmer.user.full_name,
            "email": obj.farmer.user.email,
            "farm_name": obj.farmer.farm_name,
            "farm_location": obj.farmer.farm_location,
        }

    def get_produce_details(self, obj):
        return {
            "id": str(obj.produce.id),
            "name": obj.produce.produce_name,
            "category": obj.produce.category,
            "unit_price": str(obj.produce.unit_price),
            "quantity_available": obj.produce.quantity_available,
        }

    def get_orders(self, obj):
        orders = obj.orders.all()[:10]  # Last 10 orders
        return SubscriptionOrderSerializer(orders, many=True).data


class SubscriptionOrderSerializer(serializers.ModelSerializer):
    subscription_id = serializers.CharField(source="subscription.id", read_only=True)
    produce_name = serializers.CharField(
        source="subscription.produce.produce_name", read_only=True
    )

    class Meta:
        model = SubscriptionOrder
        fields = [
            "id",
            "subscription",
            "subscription_id",
            "produce_name",
            "order_id",
            "quantity",
            "unit_price",
            "total_amount",
            "order_status",
            "scheduled_date",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "order_id",
        ]


class SubscriptionOrderDetailSerializer(serializers.ModelSerializer):
    subscription_details = serializers.SerializerMethodField(read_only=True)
    payment_details = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = SubscriptionOrder
        fields = [
            "id",
            "subscription",
            "subscription_details",
            "order_id",
            "quantity",
            "unit_price",
            "total_amount",
            "order_status",
            "scheduled_date",
            "payment_details",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "order_id",
        ]

    def get_subscription_details(self, obj):
        return {
            "id": str(obj.subscription.id),
            "buyer": obj.subscription.buyer.user.full_name,
            "farmer": obj.subscription.farmer.user.full_name,
            "frequency": obj.subscription.frequency,
        }

    def get_payment_details(self, obj):
        try:
            payment = obj.payment
            return {
                "id": str(payment.id),
                "amount": str(payment.amount),
                "status": payment.payment_status,
                "method": payment.payment_method,
                "date": payment.payment_date,
            }
        except:
            return None


class SubscriptionPaymentSerializer(serializers.ModelSerializer):
    subscription_order_id = serializers.CharField(
        source="subscription_order.id", read_only=True
    )
    order_amount = serializers.DecimalField(
        source="subscription_order.total_amount",
        read_only=True,
        max_digits=10,
        decimal_places=2,
    )

    class Meta:
        model = SubscriptionPayment
        fields = [
            "id",
            "subscription_order",
            "subscription_order_id",
            "order_amount",
            "amount",
            "payment_status",
            "payment_method",
            "payment_date",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "payment_date",
        ]
