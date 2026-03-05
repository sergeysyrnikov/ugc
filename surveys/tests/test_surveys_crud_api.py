"""Tests for surveys CRUD API (staff-only ModelViewSets)."""

from __future__ import annotations

from typing import Any

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from surveys.models import (
    Answer,
    Question,
    QuestionTemplate,
    Submission,
    SubmissionAnswer,
    Survey,
)


class SurveysCrudApiTests(APITestCase):
    """Permission and CRUD tests for staff-only surveys API."""

    def _create_user(
        self,
        email: str = "user@example.com",
        password: str = "test-password",
        is_staff: bool = False,
    ) -> User:
        return User.objects.create_user(
            email=email,
            password=password,
            display_name="User",
            is_staff=is_staff,
        )

    def _authenticate(self, user: User, password: str = "test-password") -> None:
        url = reverse("token_obtain_pair")
        response = self.client.post(
            url,
            {"email": user.email, "password": password},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token = response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_surveys_list_returns_401_without_auth(self) -> None:
        url = reverse("survey-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_surveys_list_returns_403_for_non_staff(self) -> None:
        user = self._create_user()
        self._authenticate(user)
        url = reverse("survey-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_can_list_create_retrieve_update_delete_survey(self) -> None:
        staff = self._create_user(email="staff@example.com", is_staff=True)
        self._authenticate(staff)

        list_url = reverse("survey-list")
        list_resp = self.client.get(list_url)
        self.assertEqual(list_resp.status_code, status.HTTP_200_OK)
        self.assertIsInstance(list_resp.data, list)

        create_payload: dict[str, Any] = {
            "title": "New Survey",
            "description": "Desc",
            "status": "draft",
        }
        create_resp = self.client.post(list_url, create_payload, format="json")
        self.assertEqual(create_resp.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", create_resp.data)
        self.assertEqual(create_resp.data["title"], create_payload["title"])
        survey_id = create_resp.data["id"]

        detail_url = reverse("survey-detail", kwargs={"pk": survey_id})
        get_resp = self.client.get(detail_url)
        self.assertEqual(get_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(get_resp.data["id"], survey_id)

        patch_resp = self.client.patch(
            detail_url,
            {"title": "Updated Title"},
            format="json",
        )
        self.assertEqual(patch_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_resp.data["title"], "Updated Title")

        del_resp = self.client.delete(detail_url)
        self.assertEqual(del_resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Survey.objects.filter(pk=survey_id).exists())

    def test_staff_can_crud_question_templates(self) -> None:
        staff = self._create_user(email="staff@example.com", is_staff=True)
        self._authenticate(staff)

        url = reverse("questiontemplate-list")
        create_resp = self.client.post(
            url,
            {"text": "Template text"},
            format="json",
        )
        self.assertEqual(create_resp.status_code, status.HTTP_201_CREATED)
        pk = create_resp.data["id"]
        self.client.get(reverse("questiontemplate-detail", kwargs={"pk": pk}))
        self.client.patch(
            reverse("questiontemplate-detail", kwargs={"pk": pk}),
            {"text": "Updated"},
            format="json",
        )
        del_resp = self.client.delete(
            reverse("questiontemplate-detail", kwargs={"pk": pk})
        )
        self.assertEqual(del_resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(QuestionTemplate.objects.filter(pk=pk).exists())

    def test_staff_can_crud_questions(self) -> None:
        staff = self._create_user(email="staff@example.com", is_staff=True)
        self._authenticate(staff)
        survey = Survey.objects.create(title="S", author=staff)

        url = reverse("question-list")
        create_resp = self.client.post(
            url,
            {"survey": survey.id, "text": "Q1", "order": 1},
            format="json",
        )
        self.assertEqual(create_resp.status_code, status.HTTP_201_CREATED)
        pk = create_resp.data["id"]
        self.client.get(reverse("question-detail", kwargs={"pk": pk}))
        self.client.delete(reverse("question-detail", kwargs={"pk": pk}))
        self.assertFalse(Question.objects.filter(pk=pk).exists())

    def test_staff_can_crud_answers(self) -> None:
        staff = self._create_user(email="staff@example.com", is_staff=True)
        self._authenticate(staff)
        survey = Survey.objects.create(title="S", author=staff)
        question = Question.objects.create(survey=survey, text="Q", order=1)

        url = reverse("answer-list")
        create_resp = self.client.post(
            url,
            {"question": question.id, "text": "A1", "order": 1},
            format="json",
        )
        self.assertEqual(create_resp.status_code, status.HTTP_201_CREATED)
        pk = create_resp.data["id"]
        self.client.get(reverse("answer-detail", kwargs={"pk": pk}))
        self.client.delete(reverse("answer-detail", kwargs={"pk": pk}))
        self.assertFalse(Answer.objects.filter(pk=pk).exists())

    def test_staff_can_crud_submissions(self) -> None:
        staff = self._create_user(email="staff@example.com", is_staff=True)
        self._authenticate(staff)
        survey = Survey.objects.create(title="S", author=staff)

        url = reverse("submission-list")
        create_resp = self.client.post(
            url,
            {"survey": survey.id},
            format="json",
        )
        self.assertEqual(create_resp.status_code, status.HTTP_201_CREATED)
        pk = create_resp.data["id"]
        self.client.get(reverse("submission-detail", kwargs={"pk": pk}))
        self.client.delete(reverse("submission-detail", kwargs={"pk": pk}))
        self.assertFalse(Submission.objects.filter(pk=pk).exists())

    def test_staff_can_crud_submission_answers(self) -> None:
        staff = self._create_user(email="staff@example.com", is_staff=True)
        self._authenticate(staff)
        survey = Survey.objects.create(title="S", author=staff)
        question = Question.objects.create(survey=survey, text="Q", order=1)
        answer = Answer.objects.create(question=question, text="A", order=1)
        submission = Submission.objects.create(survey=survey)

        url = reverse("submissionanswer-list")
        create_resp = self.client.post(
            url,
            {
                "submission": submission.id,
                "question": question.id,
                "answer": answer.id,
            },
            format="json",
        )
        self.assertEqual(create_resp.status_code, status.HTTP_201_CREATED)
        pk = create_resp.data["id"]
        self.client.get(reverse("submissionanswer-detail", kwargs={"pk": pk}))
        self.client.delete(reverse("submissionanswer-detail", kwargs={"pk": pk}))
        self.assertFalse(SubmissionAnswer.objects.filter(pk=pk).exists())

    def test_survey_create_defaults_author_to_request_user(self) -> None:
        staff = self._create_user(email="staff@example.com", is_staff=True)
        self._authenticate(staff)

        create_resp = self.client.post(
            reverse("survey-list"),
            {"title": "No author", "status": "draft"},
            format="json",
        )
        self.assertEqual(create_resp.status_code, status.HTTP_201_CREATED)
        survey = Survey.objects.get(pk=create_resp.data["id"])
        self.assertEqual(survey.author_id, staff.id)
