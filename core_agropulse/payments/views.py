import requests
import hashlib
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend

from core_agropulse.payments.models import Payment, EscrowAccount, PaymentSplit, Payout
from core_agropulse.payments.serializers import (
    PaymentSerializer,
    PaymentDetailSerializer,
    EscrowAccountSerializer,
    PaymentSplitSerializer,
    PayoutSerializer,
    PayoutDetailSerializer,
)
from core_agropulse.orders.models import Order
from core_agropulse.accounts.models import FarmerProfile, TransporterProfile


class Squad:
    """Squad payment gateway integration"""

    # BASE_URL = "https://api.squadco.com"
    BASE_URL = "https://sandbox-api-d.squadco.com"

    def __init__(self):
        self.api_key = settings.SQUAD_SECRET_KEY
        self.merchant_id = settings.SQUAD_MERCHANT_ID
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def initialize_payment(self, amount, order_id, email, full_name):
        """Initialize payment with Squad"""
        url = f"{self.BASE_URL}/transaction/Initiate"
        payload = {
            "email": email,
            "amount": int(amount * 100),
            "currency": "NGN",
            "initiate_type": "inline",
            "callback_url": "https://yourdomain.com/api/webhooks/squad/",
            "payment_channels": ["card", "bank", "transfer", "ussd"],
            "metadata": {"name": full_name, "order_id": order_id},
            "pass_charge": False,
        }

        try:
            response = requests.post(
                url, json=payload, headers=self.headers, timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise ValidationError(f"Squad payment initialization failed: {str(e)}")

    def verify_payment(self, squad_transaction_id):
        """Verify payment status with Squad"""
        url = f"{self.BASE_URL}/transaction/verify/{squad_transaction_id}"

        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise ValidationError(f"Payment verification failed: {str(e)}")

    def verify_webhook_signature(self, body, signature):
        """Verify Squad webhook signature"""
        hash_object = hashlib.sha512(body + self.api_key.encode())
        computed_hash = hash_object.hexdigest()
        return computed_hash == signature


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["payment_status"]
    ordering_fields = ["created_at", "amount"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return PaymentDetailSerializer
        return PaymentSerializer

    def get_queryset(self):
        """Filter payments based on user role"""
        user = self.request.user
        queryset = Payment.objects.all()

        if user.is_staff:
            return queryset

        # Buyer can see payments for their orders
        try:
            from core_agropulse.accounts.models import BuyerProfile

            buyer = BuyerProfile.objects.get(user=user)
            return queryset.filter(order__buyer=buyer)
        except:
            pass

        # Farmer can see payments for their orders
        try:
            farmer = FarmerProfile.objects.get(user=user)
            return queryset.filter(order__farmer=farmer)
        except:
            pass

        return Payment.objects.none()

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def initialize_payment(self, request):
        """Initialize payment for an order"""
        order_id = request.data.get("order_id")

        if not order_id:
            return Response(
                {"error": "order_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response(
                {"error": "Order not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check if payment already exists
        if hasattr(order, "payment"):
            if order.payment.payment_status == "SUCCESS":
                return Response(
                    {"error": "Order already paid"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Create payment record
        payment = Payment.objects.create(
            order=order,
            amount=order.total,
            escrow_enabled=True,
        )

        # Initialize Squad payment
        squad = Squad()
        try:
            squad_response = squad.initialize_payment(
                order.total,
                order.id,
                order.buyer.user.email,
                order.buyer.user.full_name,
            )

            payment.squad_transaction_id = squad_response.get("transaction_reference")
            payment.save()

            return Response(
                {
                    "payment_id": str(payment.id),
                    "squad_transaction_id": payment.squad_transaction_id,
                    "authorization_url": squad_response.get("authorization_url"),
                    "amount": str(payment.amount),
                },
                status=status.HTTP_201_CREATED,
            )
        except ValidationError as e:
            payment.delete()
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def verify_payment(self, request, pk=None):
        """Verify and confirm payment"""
        payment = self.get_object()

        if not payment.squad_transaction_id:
            return Response(
                {"error": "No Squad transaction ID found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        squad = Squad()
        try:
            squad_response = squad.verify_payment(payment.squad_transaction_id)

            if squad_response.get("status") == "success":
                payment.payment_status = "SUCCESS"
                payment.payment_method = squad_response.get("payment_method", "card")
                payment.save()

                # Create escrow and split if enabled
                if payment.escrow_enabled:
                    self._create_escrow(payment)
                    self._create_payment_split(payment)

                serializer = self.get_serializer(payment)
                return Response(serializer.data)
            else:
                payment.payment_status = "FAILED"
                payment.save()
                return Response(
                    {"error": "Payment verification failed"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except ValidationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def webhook_callback(self, request):
        """Handle Squad webhook callback"""
        squad = Squad()

        # Get signature from headers
        signature = request.META.get("HTTP_X_SQUAD_SIGNATURE", "")
        body = request.body

        # Verify webhook signature
        if not squad.verify_webhook_signature(body, signature):
            return Response(
                {"error": "Invalid signature"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            data = request.data
            transaction_ref = data.get("transaction_reference")
            status_value = data.get("status")

            # Find payment by Squad transaction ID
            try:
                payment = Payment.objects.get(squad_transaction_id=transaction_ref)
            except Payment.DoesNotExist:
                return Response(
                    {"error": "Payment not found"}, status=status.HTTP_404_NOT_FOUND
                )

            if status_value == "success":
                payment.payment_status = "SUCCESS"
                payment.payment_method = data.get("payment_method", "card")
                payment.save()

                # Create escrow and split
                if payment.escrow_enabled:
                    self._create_escrow(payment)
                    self._create_payment_split(payment)

            elif status_value == "failed":
                payment.payment_status = "FAILED"
                payment.save()

            return Response({"status": "received"})
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def _create_escrow(self, payment):
        """Create escrow account for payment"""
        if hasattr(payment, "escrow"):
            return

        EscrowAccount.objects.create(
            payment=payment,
            farmer=payment.order.farmer,
            amount_held=payment.amount,
        )

    def _create_payment_split(self, payment):
        """Create payment split for farmer, rider, and platform"""
        if hasattr(payment, "split"):
            return

        # Calculate split: 80% farmer, 10% rider, 10% platform
        farmer_amount = payment.amount * Decimal("0.80")
        rider_amount = payment.amount * Decimal("0.10")
        platform_fee = payment.amount * Decimal("0.10")

        PaymentSplit.objects.create(
            payment=payment,
            farmer_amount=farmer_amount,
            rider_amount=rider_amount,
            platform_fee=platform_fee,
        )

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def pending_payments(self, request):
        """Get pending payments"""
        payments = Payment.objects.filter(payment_status="PENDING")
        serializer = self.get_serializer(payments, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def my_payments(self, request):
        """Get current user's payments"""
        user = request.user
        payments = []

        try:
            from core_agropulse.accounts.models import BuyerProfile

            buyer = BuyerProfile.objects.get(user=user)
            payments = Payment.objects.filter(order__buyer=buyer)
        except:
            pass

        serializer = self.get_serializer(payments, many=True)
        return Response(serializer.data)


class EscrowAccountViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only viewset for escrow accounts"""

    queryset = EscrowAccount.objects.all()
    serializer_class = EscrowAccountSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["release_status", "farmer"]
    ordering_fields = ["created_at", "amount_held"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """Filter escrow accounts based on user role"""
        user = self.request.user
        queryset = EscrowAccount.objects.all()

        if user.is_staff:
            return queryset

        try:
            farmer = FarmerProfile.objects.get(user=user)
            return queryset.filter(farmer=farmer)
        except:
            pass

        return EscrowAccount.objects.none()

    @action(detail=True, methods=["post"])
    def release_funds(self, request, pk=None):
        """Release escrowed funds after delivery confirmation"""
        escrow = self.get_object()

        if escrow.release_status != "HELD":
            return Response(
                {"error": f"Escrow is already {escrow.release_status}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if delivery is confirmed
        try:
            delivery = escrow.payment.order.delivery
            if delivery.delivery_status != "DELIVERED":
                return Response(
                    {"error": "Delivery not confirmed yet"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except:
            return Response(
                {"error": "Delivery record not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        escrow.release_status = "RELEASED"
        escrow.released_at = timezone.now()
        escrow.save()

        # Create farmer payout
        split = escrow.payment.split
        Payout.objects.create(
            payment=escrow.payment,
            farmer=escrow.farmer,
            payout_type="FARMER",
            amount=split.farmer_amount,
            payout_status="PENDING",
        )

        return Response(EscrowAccountSerializer(escrow).data)

    @action(detail=False, methods=["get"])
    def held_funds(self, request):
        """Get all held escrowed funds"""
        escrows = EscrowAccount.objects.filter(release_status="HELD")
        serializer = self.get_serializer(escrows, many=True)
        return Response(serializer.data)


class PaymentSplitViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only viewset for payment splits"""

    queryset = PaymentSplit.objects.all()
    serializer_class = PaymentSplitSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ["created_at", "farmer_amount"]
    ordering = ["-created_at"]


class PayoutViewSet(viewsets.ModelViewSet):
    """Viewset for managing payouts"""

    queryset = Payout.objects.all()
    serializer_class = PayoutSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["payout_status", "payout_type"]
    ordering_fields = ["created_at", "amount"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return PayoutDetailSerializer
        return PayoutSerializer

    def get_queryset(self):
        """Filter payouts based on user role"""
        user = self.request.user
        queryset = Payout.objects.all()

        if user.is_staff:
            return queryset

        try:
            farmer = FarmerProfile.objects.get(user=user)
            return queryset.filter(farmer=farmer)
        except:
            pass

        try:
            rider = TransporterProfile.objects.get(user=user)
            return queryset.filter(rider=rider)
        except:
            pass

        return Payout.objects.none()

    @action(detail=False, methods=["post"])
    def process_farmer_payouts(self, request):
        """Process all pending farmer payouts"""
        if not request.user.is_staff:
            return Response(
                {"error": "Only admins can process payouts"},
                status=status.HTTP_403_FORBIDDEN,
            )

        payouts = Payout.objects.filter(payout_status="PENDING", payout_type="FARMER")

        processed = []
        for payout in payouts:
            payout.payout_status = "PROCESSING"
            payout.save()
            processed.append(str(payout.id))

        return Response(
            {
                "processed_count": len(processed),
                "payout_ids": processed,
            }
        )

    @action(detail=False, methods=["post"])
    def process_rider_payouts(self, request):
        """Process all pending rider payouts"""
        if not request.user.is_staff:
            return Response(
                {"error": "Only admins can process payouts"},
                status=status.HTTP_403_FORBIDDEN,
            )

        payouts = Payout.objects.filter(payout_status="PENDING", payout_type="RIDER")

        processed = []
        for payout in payouts:
            payout.payout_status = "PROCESSING"
            payout.save()
            processed.append(str(payout.id))

        return Response(
            {
                "processed_count": len(processed),
                "payout_ids": processed,
            }
        )

    @action(detail=True, methods=["post"])
    def mark_completed(self, request, pk=None):
        """Mark payout as completed"""
        payout = self.get_object()

        if payout.payout_status not in ["PROCESSING", "PENDING"]:
            return Response(
                {"error": f"Cannot complete payout in {payout.payout_status} status"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        bank_reference = request.data.get("bank_reference")
        if not bank_reference:
            return Response(
                {"error": "bank_reference is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payout.payout_status = "COMPLETED"
        payout.bank_reference = bank_reference
        payout.completed_at = timezone.now()
        payout.save()

        # Update split processing status
        split = payout.payment.split
        if payout.payout_type == "FARMER":
            split.farmer_processed = True
        elif payout.payout_type == "RIDER":
            split.rider_processed = True
        split.save()

        return Response(self.get_serializer(payout).data)

    @action(detail=False, methods=["get"])
    def pending_farmer_payouts(self, request):
        """Get pending farmer payouts"""
        if not request.user.is_staff:
            return Response(
                {"error": "Only admins can view all payouts"},
                status=status.HTTP_403_FORBIDDEN,
            )

        payouts = Payout.objects.filter(payout_status="PENDING", payout_type="FARMER")
        serializer = self.get_serializer(payouts, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def pending_rider_payouts(self, request):
        """Get pending rider payouts"""
        if not request.user.is_staff:
            return Response(
                {"error": "Only admins can view all payouts"},
                status=status.HTTP_403_FORBIDDEN,
            )

        payouts = Payout.objects.filter(payout_status="PENDING", payout_type="RIDER")
        serializer = self.get_serializer(payouts, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def my_payouts(self, request):
        """Get current user's payouts"""
        user = request.user
        payouts = []

        try:
            farmer = FarmerProfile.objects.get(user=user)
            payouts = Payout.objects.filter(farmer=farmer)
        except:
            pass

        try:
            rider = TransporterProfile.objects.get(user=user)
            payouts = list(payouts) + list(Payout.objects.filter(rider=rider))
        except:
            pass

        serializer = self.get_serializer(payouts, many=True)
        return Response(serializer.data)
