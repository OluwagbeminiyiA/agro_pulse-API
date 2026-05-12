from rest_framework import serializers
from core_agropulse.payments.models import (
    Payment,
    EscrowAccount,
    PaymentSplit,
    Payout,
    VirtualAccount,
    VirtualAccountTransaction,
)


class PaymentSerializer(serializers.ModelSerializer):
    order_id = serializers.CharField(source="order.id", read_only=True)
    buyer_name = serializers.CharField(
        source="order.buyer.user.full_name", read_only=True
    )
    farmer_name = serializers.CharField(
        source="order.farmer.user.full_name", read_only=True
    )
    order_total = serializers.DecimalField(
        source="order.total", read_only=True, max_digits=10, decimal_places=2
    )

    class Meta:
        model = Payment
        fields = [
            "id",
            "buyer",
            "order",
            "order_id",
            "buyer_name",
            "farmer_name",
            "order_total",
            "email",
            "squad_transaction_id",
            "payment_method",
            "payment_status",
            "amount",
            "currency",
            "channel",
            "escrow_enabled",
            "webhook_recieved",
            "webhook_verified",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "squad_transaction_id"]


class PaymentDetailSerializer(serializers.ModelSerializer):
    order_details = serializers.SerializerMethodField(read_only=True)
    escrow_details = serializers.SerializerMethodField(read_only=True)
    split_details = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id",
            "order",
            "order_details",
            "squad_transaction_id",
            "payment_method",
            "payment_status",
            "amount",
            "escrow_enabled",
            "escrow_details",
            "split_details",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_order_details(self, obj):
        return {
            "id": str(obj.order.id),
            "buyer": obj.order.buyer.user.full_name,
            "farmer": obj.order.farmer.user.full_name,
            "total": str(obj.order.total),
            "status": obj.order.order_status,
        }

    def get_escrow_details(self, obj):
        try:
            escrow = obj.escrow
            return {
                "id": str(escrow.id),
                "amount_held": str(escrow.amount_held),
                "release_status": escrow.release_status,
                "released_at": escrow.released_at,
            }
        except:
            return None

    def get_split_details(self, obj):
        try:
            split = obj.split
            return {
                "id": str(split.id),
                "farmer_amount": str(split.farmer_amount),
                "rider_amount": str(split.rider_amount),
                "platform_fee": str(split.platform_fee),
                "farmer_processed": split.farmer_processed,
                "rider_processed": split.rider_processed,
            }
        except:
            return None


class EscrowAccountSerializer(serializers.ModelSerializer):
    farmer_name = serializers.CharField(source="farmer.user.full_name", read_only=True)
    payment_id = serializers.CharField(source="payment.id", read_only=True)

    class Meta:
        model = EscrowAccount
        fields = [
            "id",
            "payment",
            "payment_id",
            "farmer",
            "farmer_name",
            "amount_held",
            "release_status",
            "released_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class PaymentSplitSerializer(serializers.ModelSerializer):
    payment_id = serializers.CharField(source="payment.id", read_only=True)

    class Meta:
        model = PaymentSplit
        fields = [
            "id",
            "payment",
            "payment_id",
            "farmer_amount",
            "rider_amount",
            "platform_fee",
            "farmer_processed",
            "rider_processed",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class PayoutSerializer(serializers.ModelSerializer):
    farmer_name = serializers.CharField(
        source="farmer.user.full_name", read_only=True, allow_null=True
    )
    rider_name = serializers.CharField(
        source="rider.user.full_name", read_only=True, allow_null=True
    )
    payment_id = serializers.CharField(source="payment.id", read_only=True)

    class Meta:
        model = Payout
        fields = [
            "id",
            "payment",
            "payment_id",
            "farmer",
            "farmer_name",
            "rider",
            "rider_name",
            "payout_type",
            "amount",
            "payout_status",
            "bank_reference",
            "completed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "completed_at"]


class PayoutDetailSerializer(serializers.ModelSerializer):
    farmer_details = serializers.SerializerMethodField(read_only=True)
    rider_details = serializers.SerializerMethodField(read_only=True)
    payment_info = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Payout
        fields = [
            "id",
            "payment",
            "payment_info",
            "farmer_details",
            "rider_details",
            "payout_type",
            "amount",
            "payout_status",
            "bank_reference",
            "completed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_farmer_details(self, obj):
        if obj.farmer:
            return {
                "id": str(obj.farmer.id),
                "name": obj.farmer.user.full_name,
                "email": obj.farmer.user.email,
                "farm_name": obj.farmer.farm_name,
            }
        return None

    def get_rider_details(self, obj):
        if obj.rider:
            return {
                "id": str(obj.rider.id),
                "name": obj.rider.user.full_name,
                "email": obj.rider.user.email,
                "vehicle_type": obj.rider.vehicle_type,
            }
        return None

    def get_payment_info(self, obj):
        return {
            "id": str(obj.payment.id),
            "amount": str(obj.payment.amount),
            "status": obj.payment.payment_status,
        }


class VirtualAccountSerializer(serializers.ModelSerializer):
    farmer_name = serializers.CharField(
        source="farmer.user.full_name", read_only=True, allow_null=True
    )
    transporter_name = serializers.CharField(
        source="transporter.user.full_name", read_only=True, allow_null=True
    )

    class Meta:
        model = VirtualAccount
        fields = [
            "id",
            "transporter",
            "transporter_name",
            "farmer",
            "farmer_name",
            "virtual_account_number",
            "bank_name",
            "account_name",
            "first_name",
            "last_name",
            "email",
            "mobile_num",
            "bvn",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class VirtualAccountDetailSerializer(serializers.ModelSerializer):
    farmer_details = serializers.SerializerMethodField(read_only=True)
    transporter_details = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = VirtualAccount
        fields = [
            "id",
            "transporter",
            "transporter_details",
            "farmer",
            "farmer_details",
            "virtual_account_number",
            "bank_name",
            "account_name",
            "first_name",
            "last_name",
            "email",
            "mobile_num",
            "bvn",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_farmer_details(self, obj):
        if obj.farmer:
            return {
                "id": str(obj.farmer.id),
                "name": obj.farmer.user.full_name,
                "email": obj.farmer.user.email,
                "farm_name": obj.farmer.farm_name,
            }
        return None

    def get_transporter_details(self, obj):
        if obj.transporter:
            return {
                "id": str(obj.transporter.id),
                "name": obj.transporter.user.full_name,
                "email": obj.transporter.user.email,
                "vehicle_type": obj.transporter.vehicle_type,
            }
        return None


class VirtualAccountTransactionSerializer(serializers.ModelSerializer):
    virtual_account_number = serializers.CharField(
        source="virtual_account.virtual_account_number", read_only=True
    )
    account_owner = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = VirtualAccountTransaction
        fields = [
            "id",
            "virtual_account",
            "virtual_account_number",
            "account_owner",
            "transaction_reference",
            "pricipal_amount",
            "settled_amount",
            "fee",
            "sender",
            "remarks",
            "currency",
            "transaction_date",
            "webhook_processed",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_account_owner(self, obj):
        if obj.virtual_account.farmer:
            return {
                "type": "farmer",
                "name": obj.virtual_account.farmer.user.full_name,
                "farm_name": obj.virtual_account.farmer.farm_name,
            }
        elif obj.virtual_account.transporter:
            return {
                "type": "transporter",
                "name": obj.virtual_account.transporter.user.full_name,
                "vehicle_type": obj.virtual_account.transporter.vehicle_type,
            }
        return None
