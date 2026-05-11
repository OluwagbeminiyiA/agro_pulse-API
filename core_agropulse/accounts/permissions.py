from rest_framework.permissions import BasePermission


class IsOTPVerified(BasePermission):
    """
    Custom permission to only allow OTP-verified users.
    """

    message = "OTP Verification required"

    def has_permission(self, request, view):
        return (
            request.user and request.user.is_authenticated and request.user.is_verified
        )
