from __future__ import annotations

from django.urls import path

from accounts.views import (
    UserListCreateAPIView,
    UserMeAPIView,
    UserRetrieveUpdateDestroyAPIView,
)


urlpatterns = [
    path(
        "",
        UserListCreateAPIView.as_view(),
        name="user-list-create",
    ),
    path(
        "me/",
        UserMeAPIView.as_view(),
        name="user-me",
    ),
    path(
        "<int:pk>/",
        UserRetrieveUpdateDestroyAPIView.as_view(),
        name="user-detail",
    ),
]
