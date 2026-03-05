from __future__ import annotations

from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsSelfOrStaff
from accounts.serializers import (
    UserReadSerializer,
    UserRegistrationSerializer,
    UserUpdateSerializer,
)


User = get_user_model()


class UserListCreateAPIView(generics.ListCreateAPIView[User]):
    """List users for admins and handle open registration."""

    queryset = User.objects.all().order_by("id")

    def get_permissions(self) -> list[permissions.BasePermission]:
        if self.request.method == "POST":
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), permissions.IsAdminUser()]

    def get_serializer_class(self) -> type[UserReadSerializer] | type[UserRegistrationSerializer]:
        if self.request.method == "POST":
            return UserRegistrationSerializer
        return UserReadSerializer


class UserMeAPIView(APIView):
    """Retrieve the profile of the currently authenticated user."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request) -> Response:
        serializer = UserReadSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request: Request) -> Response:
        serializer = UserUpdateSerializer(
            instance=request.user,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        read_serializer = UserReadSerializer(user)
        return Response(read_serializer.data, status=status.HTTP_200_OK)


class UserRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView[User]):
    """Retrieve, update and delete individual users."""

    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsSelfOrStaff]

    def get_serializer_class(self) -> type[UserReadSerializer] | type[UserUpdateSerializer]:
        if self.request.method in ("PATCH", "PUT"):
            return UserUpdateSerializer
        return UserReadSerializer

    def delete(self, request: Request, *args, **kwargs) -> Response:
        if not request.user.is_staff:
            return Response(
                data={"detail": "Only staff users can delete accounts."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().delete(request, *args, **kwargs)

