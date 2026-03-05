from __future__ import annotations

from typing import Any

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


User = get_user_model()


class UsersApiTests(APITestCase):
    """Integration tests for the users CRUD API."""

    def _create_user(
        self,
        email: str = "user@example.com",
        password: str = "test-password",
        display_name: str = "Test User",
        is_staff: bool = False,
    ) -> User:
        return User.objects.create_user(
            email=email,
            password=password,
            display_name=display_name,
            is_staff=is_staff,
        )

    def _obtain_access_token(self, email: str, password: str) -> str:
        url = reverse("token_obtain_pair")
        data: dict[str, Any] = {"email": email, "password": password}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        return str(response.data["access"])

    def _authenticate_client(self, email: str, password: str) -> None:
        token = self._obtain_access_token(email=email, password=password)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_registration_creates_user_with_safe_defaults(self) -> None:
        url = reverse("user-list-create")
        payload: dict[str, Any] = {
            "email": "newuser@example.com",
            "display_name": "New User",
            "password": "strong-password",
        }

        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)

        user = User.objects.get(email=payload["email"])
        self.assertTrue(user.check_password(payload["password"]))
        self.assertFalse(user.is_staff)
        self.assertTrue(user.is_active)

        self.assertIn("id", response.data)
        self.assertEqual(response.data["email"], payload["email"])
        self.assertEqual(response.data["display_name"], payload["display_name"])
        self.assertIn("is_active", response.data)
        self.assertIn("is_staff", response.data)
        self.assertIn("date_joined", response.data)
        self.assertNotIn("password", response.data)

    def test_registration_ignores_admin_flags_from_anonymous(self) -> None:
        url = reverse("user-list-create")
        payload: dict[str, Any] = {
            "email": "unsafe@example.com",
            "display_name": "Unsafe User",
            "password": "strong-password",
            "is_staff": True,
            "is_active": False,
        }

        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(email=payload["email"])
        self.assertFalse(user.is_staff)
        self.assertTrue(user.is_active)

    def test_regular_user_cannot_list_users(self) -> None:
        user = self._create_user()
        self._authenticate_client(email=user.email, password="test-password")

        url = reverse("user-list-create")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_regular_user_can_access_only_own_profile(self) -> None:
        user = self._create_user()
        other = self._create_user(
            email="other@example.com",
            display_name="Other User",
        )
        self._authenticate_client(email=user.email, password="test-password")

        me_url = reverse("user-me")
        me_response = self.client.get(me_url)

        self.assertEqual(me_response.status_code, status.HTTP_200_OK)
        self.assertEqual(me_response.data["id"], user.id)

        own_detail_url = reverse("user-detail", kwargs={"pk": user.id})
        own_detail_response = self.client.get(own_detail_url)

        self.assertEqual(own_detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(own_detail_response.data["id"], user.id)

        other_detail_url = reverse("user-detail", kwargs={"pk": other.id})
        other_detail_response = self.client.get(other_detail_url)

        self.assertEqual(other_detail_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_regular_user_can_update_only_allowed_fields_for_self(self) -> None:
        user = self._create_user()
        self._authenticate_client(email=user.email, password="test-password")

        url = reverse("user-detail", kwargs={"pk": user.id})
        payload: dict[str, Any] = {
            "display_name": "Updated Name",
            "is_staff": True,
        }

        response = self.client.patch(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user.refresh_from_db()
        self.assertEqual(user.display_name, payload["display_name"])
        self.assertFalse(user.is_staff)

    def test_regular_user_cannot_delete_any_user(self) -> None:
        user = self._create_user()
        other = self._create_user(
            email="other@example.com",
            display_name="Other User",
        )
        self._authenticate_client(email=user.email, password="test-password")

        own_url = reverse("user-detail", kwargs={"pk": user.id})
        own_response = self.client.delete(own_url)

        self.assertEqual(own_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(User.objects.filter(id=user.id).exists())

        other_url = reverse("user-detail", kwargs={"pk": other.id})
        other_response = self.client.delete(other_url)

        self.assertEqual(other_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(User.objects.filter(id=other.id).exists())

    def test_admin_can_list_and_manage_users(self) -> None:
        admin = self._create_user(
            email="admin@example.com",
            is_staff=True,
            display_name="Admin",
        )
        regular = self._create_user(
            email="member@example.com",
            display_name="Member",
        )
        self._authenticate_client(email=admin.email, password="test-password")

        list_url = reverse("user-list-create")
        list_response = self.client.get(list_url)

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(list_response.data), 2)

        detail_url = reverse("user-detail", kwargs={"pk": regular.id})
        detail_response = self.client.get(detail_url)

        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.data["id"], regular.id)

        patch_payload: dict[str, Any] = {"is_active": False, "is_staff": True}
        patch_response = self.client.patch(
            detail_url,
            patch_payload,
            format="json",
        )

        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)

        regular.refresh_from_db()
        self.assertFalse(regular.is_active)
        self.assertTrue(regular.is_staff)

        delete_response = self.client.delete(detail_url)

        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(id=regular.id).exists())

