from django.test import TestCase
from django.urls import resolve, reverse
from djangorestframework_mcp.test import MCPClient
from rest_framework import status

from accounts.models import User
from surveys.models import Question, Survey


class DRFMCPUrlTests(TestCase):
    """Tests for the DRF MCP /mcp/ endpoint URL routing."""

    def test_drf_mcp_endpoint_is_registered(self) -> None:
        """MCP endpoint from django-rest-framework-mcp should be resolvable at /mcp/."""
        match = resolve("/mcp/")
        self.assertIsNotNone(match.func)


class DRFMCPQuestionsListTests(TestCase):
    """MCP list_questions tool should return questions for an authenticated staff user."""

    def _create_staff_user(self) -> User:
        """Create staff user matching the requested email/password."""
        return User.objects.create_user(
            email="sergey@gmail.com",
            password="34ubitaV",
            display_name="Sergey",
            is_staff=True,
        )

    def _authenticate_mcp_client(self, client: MCPClient, user: User) -> None:
        """Obtain JWT access token and attach it to MCP client headers."""
        token_url = reverse("token_obtain_pair")
        response = client.post(
            token_url,
            {"email": user.email, "password": "34ubitaV"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        access_token = response.json()["access"]
        client.defaults["HTTP_AUTHORIZATION"] = f"Bearer {access_token}"

    def test_list_questions_returns_questions_for_staff_user(self) -> None:
        """list_questions MCP tool should return created questions."""
        user = self._create_staff_user()
        survey = Survey.objects.create(title="MCP Survey", author=user)
        Question.objects.create(survey=survey, text="Question 1", order=1)
        Question.objects.create(survey=survey, text="Question 2", order=2)

        client = MCPClient()
        self._authenticate_mcp_client(client, user)

        result = client.call_tool("list_questions")

        self.assertIsInstance(result, dict)
        structured_content = result.get("structuredContent")
        self.assertIsInstance(structured_content, list)
        self.assertEqual(len(structured_content), 2)
        texts = {item["text"] for item in structured_content}
        self.assertIn("Question 1", texts)
        self.assertIn("Question 2", texts)

