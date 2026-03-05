from django.contrib.auth import get_user_model
from django.urls import reverse
from prometheus_client import CONTENT_TYPE_LATEST
from rest_framework import status
from rest_framework.test import APITestCase

from surveys.models import Question, Submission, Survey


class MetricsEndpointTests(APITestCase):
    """Tests for the Prometheus /metrics endpoint."""

    def setUp(self) -> None:
        user_model = get_user_model()
        self.author = user_model.objects.create_user(
            email="author-metrics@example.com",
            password="password123",
        )
        self.user = user_model.objects.create_user(
            email="metrics-user@example.com",
            password="password123",
        )

        self.survey = Survey.objects.create(
            title="Metrics survey",
            author=self.author,
        )
        self.question = Question.objects.create(
            survey=self.survey,
            text="Metrics question",
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

    def test_metrics_endpoint_exposes_basic_and_custom_metrics(self) -> None:
        """/metrics should return Prometheus payload with GC and custom survey metrics."""
        url = self._build_next_question_url()
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        metrics_response = self.client.get("/metrics/")

        self.assertEqual(metrics_response.status_code, status.HTTP_200_OK)
        self.assertEqual(metrics_response["Content-Type"], CONTENT_TYPE_LATEST)

        body = metrics_response.content.decode("utf-8")
        self.assertIn("python_gc_objects_collected_total", body)
        self.assertIn("ugc_survey_requests_total", body)

