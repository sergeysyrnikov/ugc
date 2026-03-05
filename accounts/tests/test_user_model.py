from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()


class UserModelTests(TestCase):
    """Tests for the custom User model."""

    def test_create_user_with_email_successful(self) -> None:
        email = "test@example.com"
        password = "strong-password"

        user = User.objects.create_user(email=email, password=password)

        self.assertEqual(user.email, email.lower())
        self.assertTrue(user.check_password(password))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_user_without_email_raises_error(self) -> None:
        with self.assertRaises(ValueError):
            User.objects.create_user(email="", password="password")

    def test_create_superuser_has_correct_flags(self) -> None:
        email = "admin@example.com"
        password = "admin-password"

        user = User.objects.create_superuser(email=email, password=password)

        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
