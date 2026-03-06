from datetime import timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()


class JwtAuthTests(APITestCase):
    """Integration tests for JWT authentication endpoints."""

    def setUp(self) -> None:
        self.email = "authuser@example.com"
        self.password = "auth-password"
        User.objects.create_user(email=self.email, password=self.password)

    def test_obtain_jwt_token_pair(self) -> None:
        url = reverse("token_obtain_pair")
        data = {"email": self.email, "password": self.password}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_access_token_lifetime_is_10_days(self) -> None:
        url = reverse("token_obtain_pair")
        data = {"email": self.email, "password": self.password}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        access_token_raw = response.data["access"]

        access_token = AccessToken(access_token_raw)

        self.assertEqual(access_token.lifetime, timedelta(days=10))
