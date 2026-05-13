from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from core_agropulse.subscriptions.models import (
    Subscription,
    SubscriptionOrder,
    SubscriptionPayment,
)
from core_agropulse.subscriptions.serializers import (
    SubscriptionSerializer,
    SubscriptionDetailSerializer,
    SubscriptionOrderSerializer,
    SubscriptionOrderDetailSerializer,
    SubscriptionPaymentSerializer,
)
from core_agropulse.accounts.models import BuyerProfile, FarmerProfile


class SubscriptionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing subscriptions"""

    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["status", "frequency", "active"]
    ordering_fields = ["created_at", "next_expected_order_date"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return SubscriptionDetailSerializer
        return SubscriptionSerializer

    def get_queryset(self):
        """Filter subscriptions based on user role"""
        user = self.request.user
        queryset = Subscription.objects.all()

        if user.is_staff:
            return queryset

        # Buyer can see their subscriptions
        try:
            buyer = BuyerProfile.objects.get(user=user)
            return queryset.filter(buyer=buyer)
        except:
            pass

        # Farmer can see subscriptions for their produce
        try:
            farmer = FarmerProfile.objects.get(user=user)
            return queryset.filter(farmer=farmer)
        except:
            pass

        return Subscription.objects.none()

    @action(detail=True, methods=["post"])
    def pause(self, request, pk=None):
        """Pause a subscription"""
        subscription = self.get_object()
        subscription.pause()
        serializer = self.get_serializer(subscription)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def resume(self, request, pk=None):
        """Resume a paused subscription"""
        subscription = self.get_object()
        subscription.resume()
        serializer = self.get_serializer(subscription)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Cancel a subscription"""
        subscription = self.get_object()
        subscription.cancel()
        serializer = self.get_serializer(subscription)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def my_subscriptions(self, request):
        """Get current user's subscriptions"""
        user = request.user
        subscriptions = []

        try:
            buyer = BuyerProfile.objects.get(user=user)
            subscriptions = Subscription.objects.filter(buyer=buyer)
        except:
            pass

        serializer = self.get_serializer(subscriptions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def active_subscriptions(self, request):
        """Get all active subscriptions"""
        subscriptions = Subscription.objects.filter(active=True)
        serializer = self.get_serializer(subscriptions, many=True)
        return Response(serializer.data)


class SubscriptionOrderViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only viewset for subscription orders"""

    queryset = SubscriptionOrder.objects.all()
    serializer_class = SubscriptionOrderSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["subscription", "order_status"]
    ordering_fields = ["scheduled_date", "created_at"]
    ordering = ["-scheduled_date"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return SubscriptionOrderDetailSerializer
        return SubscriptionOrderSerializer

    def get_queryset(self):
        """Filter orders based on user role"""
        user = self.request.user
        queryset = SubscriptionOrder.objects.all()

        if user.is_staff:
            return queryset

        try:
            buyer = BuyerProfile.objects.get(user=user)
            return queryset.filter(subscription__buyer=buyer)
        except:
            pass

        try:
            farmer = FarmerProfile.objects.get(user=user)
            return queryset.filter(subscription__farmer=farmer)
        except:
            pass

        return SubscriptionOrder.objects.none()

    @action(detail=False, methods=["get"])
    def pending_orders(self, request):
        """Get pending subscription orders"""
        orders = SubscriptionOrder.objects.filter(order_status="PENDING")
        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def due_orders(self, request):
        """Get subscription orders due today or earlier"""
        today = timezone.now().date()
        orders = SubscriptionOrder.objects.filter(
            scheduled_date__lte=today, order_status__in=["PENDING", "CONFIRMED"]
        )
        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)


class SubscriptionPaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only viewset for subscription payments"""

    queryset = SubscriptionPayment.objects.all()
    serializer_class = SubscriptionPaymentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["payment_status"]
    ordering_fields = ["payment_date", "created_at"]
    ordering = ["-payment_date"]

    def get_queryset(self):
        """Filter payments based on user role"""
        user = self.request.user
        queryset = SubscriptionPayment.objects.all()

        if user.is_staff:
            return queryset

        try:
            buyer = BuyerProfile.objects.get(user=user)
            return queryset.filter(subscription_order__subscription__buyer=buyer)
        except:
            pass

        try:
            farmer = FarmerProfile.objects.get(user=user)
            return queryset.filter(subscription_order__subscription__farmer=farmer)
        except:
            pass

        return SubscriptionPayment.objects.none()

    @action(detail=False, methods=["get"])
    def pending_payments(self, request):
        """Get pending subscription payments"""
        payments = SubscriptionPayment.objects.filter(payment_status="PENDING")
        serializer = self.get_serializer(payments, many=True)
        return Response(serializer.data)
