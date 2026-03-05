from __future__ import annotations

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView


class IsSelfOrStaff(BasePermission):
    """Allow access to staff users or the owner of the object."""

    def has_object_permission(
        self,
        request: Request,
        view: APIView,
        obj: object,
    ) -> bool:
        user = request.user

        if not user or not user.is_authenticated:
            return False

        if user.is_staff:
            return True

        obj_id = getattr(obj, "id", None)
        return obj_id == getattr(user, "id", None)
