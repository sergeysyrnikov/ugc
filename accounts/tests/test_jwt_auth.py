from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

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
