from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend

from core_agropulse.produce.models import Produce
from core_agropulse.produce.serializers import (
    ProduceSerializer,
    ProduceDetailSerializer,
)
from core_agropulse.accounts.models import FarmerProfile


class ProduceViewSet(viewsets.ModelViewSet):
    queryset = Produce.objects.all()
    serializer_class = ProduceSerializer
    permission_classes = [AllowAny]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["category", "availability_status", "farmer"]
    search_fields = ["produce_name", "farmer__farm_name"]
    ordering_fields = ["unit_price", "created_at", "harvest_date"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ProduceDetailSerializer
        return ProduceSerializer

    def get_permissions(self):
        """
        Allow anyone to list and retrieve produces.
        Only authenticated users can create/update/delete.
        """
        if self.action in ["list", "retrieve", "available", "by_category"]:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        """Automatically set farmer to current user's farmer profile"""
        try:
            farmer_profile = FarmerProfile.objects.get(user=self.request.user)
            serializer.save(farmer=farmer_profile)
        except FarmerProfile.DoesNotExist:
            raise ValidationError("User must have a farmer profile to add produce.")

    def get_queryset(self):
        """
        Filter produces by farmer if user has a farmer profile.
        Admins can see all produces.
        """
        queryset = Produce.objects.all()
        user = self.request.user

        if user.is_authenticated and user.is_staff:
            return queryset

        # For non-staff users, they can only edit their own produces
        if self.action in ["update", "partial_update", "destroy"]:
            try:
                farmer_profile = FarmerProfile.objects.get(user=user)
                return queryset.filter(farmer=farmer_profile)
            except FarmerProfile.DoesNotExist:
                return Produce.objects.none()

        return queryset

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def my_produces(self, request):
        """Get all produces by the current user (farmer)"""
        try:
            farmer_profile = FarmerProfile.objects.get(user=request.user)
            produces = Produce.objects.filter(farmer=farmer_profile)
            serializer = self.get_serializer(produces, many=True)
            return Response(serializer.data)
        except FarmerProfile.DoesNotExist:
            return Response(
                {"error": "User does not have a farmer profile"},
                status=status.HTTP_404_NOT_FOUND,
            )

    @action(detail=False, methods=["get"])
    def available(self, request):
        """Get all available produces"""
        produces = Produce.objects.filter(availability_status="AVAILABLE")
        serializer = self.get_serializer(produces, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def by_category(self, request):
        """Get produces by category"""
        category = request.query_params.get("category", None)
        if category:
            produces = Produce.objects.filter(category=category)
            serializer = self.get_serializer(produces, many=True)
            return Response(serializer.data)
        return Response(
            {"error": "category parameter is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(detail=True, methods=["patch"], permission_classes=[IsAuthenticated])
    def update_stock(self, request, pk=None):
        """Update quantity available for a produce"""
        produce = self.get_object()
        quantity = request.data.get("quantity_available")

        if quantity is None:
            return Response(
                {"error": "quantity_available is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if quantity < 0:
            return Response(
                {"error": "quantity_available cannot be negative"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        produce.quantity_available = quantity

        # Update availability status based on quantity
        if quantity == 0:
            produce.availability_status = "SOLD_OUT"
        elif quantity < 10:  # Threshold for low stock
            produce.availability_status = "LOW_STOCK"
        else:
            produce.availability_status = "AVAILABLE"

        produce.save()
        serializer = self.get_serializer(produce)
        return Response(serializer.data)
