from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from surveys.models import Answer, Question, Submission, SubmissionAnswer, Survey


class NextQuestionAPITests(APITestCase):
    """Tests for the next-question API endpoint."""

    def setUp(self) -> None:
        user_model = get_user_model()
        self.author = user_model.objects.create_user(
            email="author@example.com",
            password="password123",
        )

        self.survey = Survey.objects.create(
            title="Simple survey",
            author=self.author,
        )

        self.question1 = Question.objects.create(
            survey=self.survey,
            text="Question 1",
            order=1,
        )
        self.question2 = Question.objects.create(
            survey=self.survey,
            text="Question 2",
            order=2,
        )
        self.question3 = Question.objects.create(
            survey=self.survey,
            text="Question 3",
            order=3,
        )

        self.submission = Submission.objects.create(
            survey=self.survey,
        )

    def _build_url(self, survey_id: int, submission_id: int) -> str:
        return reverse(
            "survey-next-question",
            kwargs={
                "survey_id": survey_id,
                "submission_id": submission_id,
            },
        )

    def test_returns_first_question_when_no_answers(self) -> None:
        url = self._build_url(self.survey.id, self.submission.id)

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["is_finished"], False)
        self.assertIsNotNone(response.data["question"])
        self.assertEqual(response.data["question"]["id"], self.question1.id)
        self.assertEqual(response.data["question"]["order"], 1)

    def test_returns_next_question_after_some_answers(self) -> None:
        answer1 = Answer.objects.create(
            question=self.question1,
            text="Answer 1",
            order=1,
        )

        SubmissionAnswer.objects.create(
            submission=self.submission,
            question=self.question1,
            answer=answer1,
        )

        url = self._build_url(self.survey.id, self.submission.id)

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["is_finished"], False)
        self.assertIsNotNone(response.data["question"])
        self.assertEqual(response.data["question"]["id"], self.question2.id)

    def test_marks_survey_as_finished_when_all_answered(self) -> None:
        for index, question in enumerate(
            (self.question1, self.question2, self.question3), start=1
        ):
            answer = Answer.objects.create(
                question=question,
                text=f"Answer {index}",
                order=1,
            )
            SubmissionAnswer.objects.create(
                submission=self.submission,
                question=question,
                answer=answer,
            )

        url = self._build_url(self.survey.id, self.submission.id)

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["is_finished"], True)
        self.assertIsNone(response.data["question"])

    def test_404_when_survey_not_found(self) -> None:
        url = self._build_url(
            survey_id=self.survey.id + 1, submission_id=self.submission.id
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_404_when_submission_not_found(self) -> None:
        url = self._build_url(
            survey_id=self.survey.id, submission_id=self.submission.id + 1
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_400_when_submission_not_for_survey(self) -> None:
        other_survey = Survey.objects.create(
            title="Other survey",
            author=self.author,
        )
        other_submission = Submission.objects.create(
            survey=other_survey,
        )

        url = self._build_url(
            survey_id=self.survey.id, submission_id=other_submission.id
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)
