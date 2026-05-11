from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django_otp.plugins.otp_email.models import EmailDevice
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from core_agropulse.accounts.models import (
    User,
    FarmerProfile,
    BuyerProfile,
    TransporterProfile,
)
from core_agropulse.accounts.serializers import (
    UserSerializer,
    UserDetailSerializer,
    FarmerProfileSerializer,
    BuyerProfileSerializer,
    TransporterProfileSerializer,
    EmailOtpVerifySerializer,
    LoginSerializer,
)


class EmailOTPRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        device, created = EmailDevice.objects.get_or_create(
            user=user, name="email", defaults={"email": user.email}
        )

        try:
            device.generate_challenge()
            return Response({"message": f"OTP sent to {user.email}"})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)


class EmailOTPVerifyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = EmailOtpVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            device = EmailDevice.objects.get(
                user=request.user,
                name="email",
            )
        except EmailDevice.DoesNotExist:
            return Response(
                {"error": "No email device found"}, status=status.HTTP_404_NOT_FOUND
            )

        if device.verify_token(serializer.validated_data["token"]):
            from django_otp import login

            login(request, device)

            return Response(
                {
                    "message": "Login verification complete",
                    "verified": request.user.is_verified(),
                }
            )
        else:
            return Response(
                {"error": "Invalid or expired token"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return UserDetailSerializer
        return UserSerializer

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def register(self, request):
        """Register a new user"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserDetailSerializer(user).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Get current user details"""
        serializer = UserDetailSerializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def login(self, request):
        """Login with email and password, returns JWT tokens"""
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": UserDetailSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )


class FarmerProfileViewSet(viewsets.ModelViewSet):
    queryset = FarmerProfile.objects.all()
    serializer_class = FarmerProfileSerializer
    # permission_classes = [IsOTPVerified]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter profiles by current user if not admin"""
        user = self.request.user
        if user.is_staff:
            return FarmerProfile.objects.all()
        return FarmerProfile.objects.filter(user=user)

    def perform_create(self, serializer):
        """Automatically set the user to the current user"""
        serializer.save(user=self.request.user)


class BuyerProfileViewSet(viewsets.ModelViewSet):
    queryset = BuyerProfile.objects.all()
    serializer_class = BuyerProfileSerializer
    # permission_classes = [IsOTPVerified]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter profiles by current user if not admin"""
        user = self.request.user
        if user.is_staff:
            return BuyerProfile.objects.all()
        return BuyerProfile.objects.filter(user=user)

    def perform_create(self, serializer):
        """Automatically set the user to the current user"""
        serializer.save(user=self.request.user)


class TransporterProfileViewSet(viewsets.ModelViewSet):
    queryset = TransporterProfile.objects.all()
    serializer_class = TransporterProfileSerializer
    # permission_classes = [IsOTPVerified]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter profiles by current user if not admin"""
        user = self.request.user
        if user.is_staff:
            return TransporterProfile.objects.all()
        return TransporterProfile.objects.filter(user=user)

    def perform_create(self, serializer):
        """Automatically set the user to the current user"""
        serializer.save(user=self.request.user)
