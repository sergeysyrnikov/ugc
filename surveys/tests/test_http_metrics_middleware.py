from django.contrib.auth import get_user_model
from django.urls import reverse
from prometheus_client import CONTENT_TYPE_LATEST
from rest_framework import status
from rest_framework.test import APITestCase

from surveys.models import Question, Submission, Survey


class HttpMetricsMiddlewareTests(APITestCase):
    """Tests for HTTP metrics middleware integration."""

    def setUp(self) -> None:
        user_model = get_user_model()
        self.author = user_model.objects.create_user(
            email="author-http-metrics@example.com",
            password="password123",
        )
        self.user = user_model.objects.create_user(
            email="http-metrics-user@example.com",
            password="password123",
        )

        self.survey = Survey.objects.create(
            title="HTTP metrics survey",
            author=self.author,
        )
        self.question = Question.objects.create(
            survey=self.survey,
            text="HTTP metrics question",
            order=1,
        )
        self.submission = Submission.objects.create(
            survey=self.survey,
        )

        self.client.force_authenticate(user=self.user)

    def _build_next_question_url(self) -> str:
        return reverse(
            "survey-next-question",
            kwargs={
                "survey_id": self.survey.id,
                "submission_id": self.submission.id,
            },
        )

    def test_http_metrics_collected_for_api_requests(self) -> None:
        """HTTP requests to API should be reflected in Prometheus HTTP metrics."""
        url = self._build_next_question_url()

        for _ in range(3):
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        metrics_response = self.client.get("/metrics/")

        self.assertEqual(metrics_response.status_code, status.HTTP_200_OK)
        self.assertEqual(metrics_response["Content-Type"], CONTENT_TYPE_LATEST)

        body = metrics_response.content.decode("utf-8")

        self.assertIn("ugc_http_requests_total", body)
        self.assertIn("ugc_http_request_latency_seconds_bucket", body)
        self.assertIn('method="GET"', body)
        self.assertIn('status_code="200"', body)

