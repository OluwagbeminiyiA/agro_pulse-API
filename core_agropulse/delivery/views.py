from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from core_agropulse.delivery.models import Delivery, RiderEarnings
from core_agropulse.delivery.serializers import (
    DeliverySerializer,
    DeliveryDetailSerializer,
    RiderEarningsSerializer,
    RiderEarningsDetailSerializer,
)
from core_agropulse.accounts.models import TransporterProfile
from core_agropulse.orders.models import Order


class DeliveryViewSet(viewsets.ModelViewSet):
    queryset = Delivery.objects.all()
    serializer_class = DeliverySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["delivery_status", "transporter"]
    search_fields = ["delivery_address", "order__buyer__business_name"]
    ordering_fields = ["created_at", "delivered_at"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return DeliveryDetailSerializer
        return DeliverySerializer

    def get_queryset(self):
        """Filter deliveries based on user role"""
        user = self.request.user
        queryset = Delivery.objects.all()

        # Admin can see all deliveries
        if user.is_staff:
            return queryset

        # Transporter can only see their own deliveries
        try:
            transporter_profile = TransporterProfile.objects.get(user=user)
            return queryset.filter(transporter=transporter_profile)
        except TransporterProfile.DoesNotExist:
            pass

        # Buyer can see deliveries for their orders
        try:
            from core_agropulse.accounts.models import BuyerProfile

            buyer_profile = BuyerProfile.objects.get(user=user)
            return queryset.filter(order__buyer=buyer_profile)
        except Exception:
            pass

        # Farmer can see deliveries for their orders
        try:
            from core_agropulse.accounts.models import FarmerProfile

            farmer_profile = FarmerProfile.objects.get(user=user)
            return queryset.filter(order__farmer=farmer_profile)
        except Exception:
            pass

        return Delivery.objects.none()

    def perform_create(self, serializer):
        """Create delivery for an order with delivery type"""
        order_id = self.request.data.get("order")
        transporter_id = self.request.data.get("transporter")

        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            raise ValidationError("Invalid order ID")

        if order.delivery_type != "DELIVERY":
            raise ValidationError("Only orders with DELIVERY type can have deliveries")

        try:
            transporter = TransporterProfile.objects.get(id=transporter_id)
        except TransporterProfile.DoesNotExist:
            raise ValidationError("Invalid transporter ID")

        serializer.save(order=order, transporter=transporter)

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def available_riders(self, request):
        """Get available transporters for pickup"""
        transporters = TransporterProfile.objects.all()
        data = []
        for transporter in transporters:
            active_deliveries = Delivery.objects.filter(
                transporter=transporter,
                delivery_status__in=["PENDING", "PICKED_UP", "IN_TRANSIT"],
            ).count()
            data.append(
                {
                    "id": str(transporter.id),
                    "name": transporter.user.full_name,
                    "email": transporter.user.email,
                    "phone": transporter.user.phone_number,
                    "vehicle_type": transporter.vehicle_type,
                    "plate_number": transporter.plate_number,
                    "service_area": transporter.service_area,
                    "active_deliveries": active_deliveries,
                    "is_available": active_deliveries
                    < 5,  # Max 5 concurrent deliveries
                }
            )
        return Response(data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def assign_rider(self, request, pk=None):
        """Assign a rider to a delivery"""
        delivery = self.get_object()
        transporter_id = request.data.get("transporter_id")

        if not transporter_id:
            return Response(
                {"error": "transporter_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            transporter = TransporterProfile.objects.get(id=transporter_id)
        except TransporterProfile.DoesNotExist:
            return Response(
                {"error": "Invalid transporter ID"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if transporter has available capacity
        active_deliveries = Delivery.objects.filter(
            transporter=transporter,
            delivery_status__in=["PENDING", "PICKED_UP", "IN_TRANSIT"],
        ).count()

        if active_deliveries >= 5:
            return Response(
                {"error": "Transporter has reached maximum delivery capacity"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        delivery.transporter = transporter
        delivery.save()
        serializer = self.get_serializer(delivery)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def pickup_confirmation(self, request, pk=None):
        """Confirm that rider has picked up the delivery"""
        delivery = self.get_object()

        if delivery.delivery_status not in ["PENDING"]:
            return Response(
                {
                    "error": f"Cannot pickup delivery in {delivery.delivery_status} status"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        delivery.delivery_status = "PICKED_UP"
        delivery.picked_up_at = timezone.now()
        delivery.save()

        serializer = self.get_serializer(delivery)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def start_transit(self, request, pk=None):
        """Mark delivery as in transit"""
        delivery = self.get_object()

        if delivery.delivery_status != "PICKED_UP":
            return Response(
                {"error": "Delivery must be picked up before transit"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        delivery.delivery_status = "IN_TRANSIT"
        delivery.save()

        serializer = self.get_serializer(delivery)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def delivery_confirmation(self, request, pk=None):
        """Confirm delivery completion and update order status"""
        delivery = self.get_object()

        if delivery.delivery_status != "IN_TRANSIT":
            return Response(
                {"error": "Delivery must be in transit to complete"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        delivery.delivery_status = "DELIVERED"
        delivery.delivered_at = timezone.now()
        delivery.save()

        # Update order status to completed
        order = delivery.order
        order.order_status = "COMPLETED"
        order.save()

        # Create earnings record for rider
        from decimal import Decimal

        base_earnings = order.total * Decimal("0.10")  # 10% of order total
        RiderEarnings.objects.create(
            transporter=delivery.transporter,
            delivery=delivery,
            earnings_amount=base_earnings,
        )

        serializer = self.get_serializer(delivery)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def my_deliveries(self, request):
        """Get all deliveries for current transporter"""
        user = request.user
        try:
            transporter = TransporterProfile.objects.get(user=user)
            deliveries = Delivery.objects.filter(transporter=transporter)
            serializer = self.get_serializer(deliveries, many=True)
            return Response(serializer.data)
        except TransporterProfile.DoesNotExist:
            return Response(
                {"error": "User is not a transporter"},
                status=status.HTTP_404_NOT_FOUND,
            )

    @action(detail=False, methods=["get"], permission_classes=[AllowAny])
    def pending_deliveries(self, request):
        """Get all pending deliveries"""
        deliveries = Delivery.objects.filter(delivery_status="PENDING")
        serializer = self.get_serializer(deliveries, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], permission_classes=[AllowAny])
    def by_status(self, request):
        """Get deliveries by status"""
        status_filter = request.query_params.get("status", None)
        if status_filter:
            deliveries = Delivery.objects.filter(delivery_status=status_filter)
            serializer = self.get_serializer(deliveries, many=True)
            return Response(serializer.data)
        return Response(
            {"error": "status parameter is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )


class RiderEarningsViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only viewset for rider earnings tracking"""

    queryset = RiderEarnings.objects.all()
    serializer_class = RiderEarningsSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["payment_status", "transporter"]
    ordering_fields = ["earnings_amount", "created_at"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return RiderEarningsDetailSerializer
        return RiderEarningsSerializer

    def get_queryset(self):
        """Filter earnings based on user role"""
        user = self.request.user
        queryset = RiderEarnings.objects.all()

        # Admin can see all earnings
        if user.is_staff:
            return queryset

        # Transporter can only see their own earnings
        try:
            transporter = TransporterProfile.objects.get(user=user)
            return queryset.filter(transporter=transporter)
        except TransporterProfile.DoesNotExist:
            pass

        return RiderEarnings.objects.none()

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def my_earnings(self, request):
        """Get earnings summary for current transporter"""
        user = request.user
        try:
            transporter = TransporterProfile.objects.get(user=user)
            earnings = RiderEarnings.objects.filter(transporter=transporter)

            total_earned = sum(e.earnings_amount for e in earnings)
            total_paid = sum(
                e.earnings_amount for e in earnings if e.payment_status == "PAID"
            )
            total_pending = sum(
                e.earnings_amount for e in earnings if e.payment_status == "PENDING"
            )
            completed_deliveries = earnings.filter(
                delivery__delivery_status="DELIVERED"
            ).count()

            return Response(
                {
                    "total_earned": str(total_earned),
                    "total_paid": str(total_paid),
                    "total_pending": str(total_pending),
                    "completed_deliveries": completed_deliveries,
                    "earnings_list": RiderEarningsSerializer(earnings, many=True).data,
                }
            )
        except TransporterProfile.DoesNotExist:
            return Response(
                {"error": "User is not a transporter"},
                status=status.HTTP_404_NOT_FOUND,
            )

    @action(detail=False, methods=["get"])
    def pending_payments(self, request):
        """Get all pending payments to riders"""
        earnings = RiderEarnings.objects.filter(payment_status="PENDING")
        serializer = self.get_serializer(earnings, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def mark_as_paid(self, request, pk=None):
        """Mark earnings as paid"""
        earning = self.get_object()

        if earning.payment_status == "PAID":
            return Response(
                {"error": "Payment already processed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        earning.payment_status = "PAID"
        earning.paid_at = timezone.now()
        earning.save()

        serializer = self.get_serializer(earning)
        return Response(serializer.data)
