from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend

from core_agropulse.orders.models import Order, OrderItem
from core_agropulse.orders.serializers import (
    OrderSerializer,
    OrderDetailWithItemsSerializer,
    OrderItemSerializer,
)
from core_agropulse.accounts.models import BuyerProfile, FarmerProfile


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["order_status", "delivery_type", "buyer", "farmer"]
    search_fields = ["buyer__business_name", "farmer__farm_name"]
    ordering_fields = ["total", "created_at"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return OrderDetailWithItemsSerializer
        return OrderSerializer

    def get_queryset(self):
        """Filter orders based on user role"""
        user = self.request.user
        queryset = Order.objects.all()

        # Admin can see all orders
        if user.is_staff:
            return queryset

        # Buyer can only see their own orders
        try:
            buyer_profile = BuyerProfile.objects.get(user=user)
            return queryset.filter(buyer=buyer_profile)
        except BuyerProfile.DoesNotExist:
            pass

        # Farmer can only see orders for their produce
        try:
            farmer_profile = FarmerProfile.objects.get(user=user)
            return queryset.filter(farmer=farmer_profile)
        except FarmerProfile.DoesNotExist:
            pass

        return Order.objects.none()

    def perform_create(self, serializer):
        """Create order from buyer's perspective"""
        buyer = self.request.data.get("buyer")
        farmer = self.request.data.get("farmer")

        try:
            buyer_profile = BuyerProfile.objects.get(id=buyer)
        except BuyerProfile.DoesNotExist:
            raise ValidationError("Invalid buyer ID")

        try:
            farmer_profile = FarmerProfile.objects.get(id=farmer)
        except FarmerProfile.DoesNotExist:
            raise ValidationError("Invalid farmer ID")

        serializer.save(buyer=buyer_profile, farmer=farmer_profile)

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def my_orders(self, request):
        """Get all orders for the current user (buyer or farmer)"""
        user = request.user

        try:
            buyer_profile = BuyerProfile.objects.get(user=user)
            orders = Order.objects.filter(buyer=buyer_profile)
            serializer = self.get_serializer(orders, many=True)
            return Response(serializer.data)
        except BuyerProfile.DoesNotExist:
            pass

        try:
            farmer_profile = FarmerProfile.objects.get(user=user)
            orders = Order.objects.filter(farmer=farmer_profile)
            serializer = self.get_serializer(orders, many=True)
            return Response(serializer.data)
        except FarmerProfile.DoesNotExist:
            pass

        return Response(
            {"error": "User does not have a buyer or farmer profile"},
            status=status.HTTP_404_NOT_FOUND,
        )

    @action(detail=True, methods=["patch"], permission_classes=[IsAuthenticated])
    def update_status(self, request, pk=None):
        """Update order status"""
        order = self.get_object()
        new_status = request.data.get("order_status")

        if new_status is None:
            return Response(
                {"error": "order_status is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate status is in choices
        valid_statuses = [
            choice[0] for choice in order._meta.get_field("order_status").choices
        ]
        if new_status not in valid_statuses:
            return Response(
                {"error": f"Invalid status. Valid options: {valid_statuses}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order.order_status = new_status
        order.save()
        serializer = self.get_serializer(order)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def pending_orders(self, request):
        """Get all pending orders"""
        orders = Order.objects.filter(order_status="PENDING")
        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def by_status(self, request):
        """Get orders by status"""
        status_filter = request.query_params.get("status", None)
        if status_filter:
            orders = Order.objects.filter(order_status=status_filter)
            serializer = self.get_serializer(orders, many=True)
            return Response(serializer.data)
        return Response(
            {"error": "status parameter is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )


class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["order", "produce"]
    ordering_fields = ["unit_price", "quantity", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """Filter order items based on user role"""
        user = self.request.user
        queryset = OrderItem.objects.all()

        # Admin can see all items
        if user.is_staff:
            return queryset

        # Buyer can only see items from their orders
        try:
            buyer_profile = BuyerProfile.objects.get(user=user)
            return queryset.filter(order__buyer=buyer_profile)
        except BuyerProfile.DoesNotExist:
            pass

        # Farmer can only see items from orders for their produce
        try:
            farmer_profile = FarmerProfile.objects.get(user=user)
            return queryset.filter(order__farmer=farmer_profile)
        except FarmerProfile.DoesNotExist:
            pass

        return OrderItem.objects.none()

    def perform_create(self, serializer):
        """Create order item - calculate subtotal automatically"""
        serializer.save()

    @action(detail=False, methods=["get"])
    def by_order(self, request):
        """Get all items for a specific order"""
        order_id = request.query_params.get("order_id", None)
        if order_id:
            items = OrderItem.objects.filter(order_id=order_id)
            serializer = self.get_serializer(items, many=True)
            return Response(serializer.data)
        return Response(
            {"error": "order_id parameter is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )
