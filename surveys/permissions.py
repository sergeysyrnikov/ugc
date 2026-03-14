from __future__ import annotations

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView


class IsSurveyAuthorOrStaff(BasePermission):
    """
    Allow list/retrieve for any authenticated user.
    Allow create for any authenticated user (author set in serializer).
    Allow update/delete only for staff or the survey author.
    """

    def has_permission(self, request: Request, view: APIView) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        # create: any authenticated user; update/delete checked in has_object_permission
        return True

    def has_object_permission(
        self,
        request: Request,
        view: APIView,
        obj: object,
    ) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_staff:
            return True
        author_id = getattr(obj, "author_id", None)
        return author_id == request.user.id
