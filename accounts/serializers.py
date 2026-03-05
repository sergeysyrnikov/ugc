from __future__ import annotations

from accounts.models import User
from rest_framework import serializers

from ugc.metrics import USER_REGISTRATION_REQUESTS_TOTAL


class UserReadSerializer(serializers.ModelSerializer):
    """Read-only serializer for user representation in the API."""

    class Meta:
        model = User
        fields = ("id", "email", "display_name", "is_active", "is_staff", "date_joined")
        read_only_fields = fields


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer used for open user registration."""

    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "display_name",
            "password",
            "is_active",
            "is_staff",
            "date_joined",
        )
        read_only_fields = ("id", "is_active", "is_staff", "date_joined")

    def create(self, validated_data: dict[str, object]) -> User:
        email = str(validated_data.get("email"))
        password = str(validated_data.get("password"))
        display_name = str(validated_data.get("display_name", ""))

        user = User.objects.create_user(
            email=email,
            password=password,
            display_name=display_name,
        )
        USER_REGISTRATION_REQUESTS_TOTAL.inc()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile and admin flags."""

    class Meta:
        model = User
        fields = ("display_name", "is_active", "is_staff")
        extra_kwargs = {
            "is_active": {"required": False},
            "is_staff": {"required": False},
        }

    def update(self, instance: User, validated_data: dict[str, object]) -> User:
        request = self.context.get("request")
        is_admin = bool(
            request is not None
            and getattr(request, "user", None) is not None
            and request.user.is_staff
        )

        if not is_admin:
            validated_data.pop("is_active", None)
            validated_data.pop("is_staff", None)

        instance.display_name = str(
            validated_data.get("display_name", instance.display_name),
        )

        if "is_active" in validated_data:
            instance.is_active = bool(validated_data["is_active"])

        if "is_staff" in validated_data:
            instance.is_staff = bool(validated_data["is_staff"])

        instance.save(update_fields=["display_name", "is_active", "is_staff"])
        return instance
