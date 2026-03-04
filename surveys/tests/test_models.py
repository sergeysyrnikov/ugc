from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

from surveys.models import (
    AnswerOption,
    Question,
    Submission,
    SubmissionAnswer,
    Survey,
    SurveyStatus,
    QuestionTemplate,
)


User = get_user_model()


class SurveyModelsTests(TestCase):
    """Tests for survey-related models."""

    def setUp(self) -> None:
        self.author = User.objects.create_user(
            email="author@example.com",
            password="password123",
        )
        self.respondent = User.objects.create_user(
            email="user@example.com",
            password="password123",
        )

    def test_create_survey_with_author(self) -> None:
        survey = Survey.objects.create(
            title="Customer satisfaction",
            description="Simple NPS survey",
            author=self.author,
            status=SurveyStatus.DRAFT,
        )

        self.assertEqual(survey.title, "Customer satisfaction")
        self.assertEqual(survey.author, self.author)
        self.assertEqual(survey.status, SurveyStatus.DRAFT)

    def test_question_and_answer_option_ordering(self) -> None:
        survey = Survey.objects.create(
            title="Ordering test",
            author=self.author,
        )

        question2 = Question.objects.create(
            survey=survey,
            text="Second question",
            order=2,
        )
        question1 = Question.objects.create(
            survey=survey,
            text="First question",
            order=1,
        )

        questions = list(survey.questions.all())
        self.assertEqual(questions[0], question1)
        self.assertEqual(questions[1], question2)

        option_b = AnswerOption.objects.create(
            question=question1,
            text="Option B",
            order=2,
        )
        option_a = AnswerOption.objects.create(
            question=question1,
            text="Option A",
            order=1,
        )

        options = list(question1.answer_options.all())
        self.assertEqual(options[0], option_a)
        self.assertEqual(options[1], option_b)

    def test_submission_and_answers_relations(self) -> None:
        survey = Survey.objects.create(
            title="Relations survey",
            author=self.author,
        )
        question = Question.objects.create(
            survey=survey,
            text="How are you?",
            order=1,
        )
        option = AnswerOption.objects.create(
            question=question,
            text="Good",
            order=1,
        )

        submission = Submission.objects.create(
            survey=survey,
            user=self.respondent,
        )
        answer = SubmissionAnswer.objects.create(
            submission=submission,
            question=question,
            answer_option=option,
        )

        self.assertEqual(submission.survey, survey)
        self.assertEqual(submission.user, self.respondent)
        self.assertEqual(answer.submission, submission)
        self.assertEqual(answer.question, question)
        self.assertEqual(answer.answer_option, option)

    def test_submission_answer_unique_per_question(self) -> None:
        survey = Survey.objects.create(
            title="Uniqueness survey",
            author=self.author,
        )
        question = Question.objects.create(
            survey=survey,
            text="Question?",
            order=1,
        )
        option = AnswerOption.objects.create(
            question=question,
            text="Yes",
            order=1,
        )
        submission = Submission.objects.create(
            survey=survey,
            user=self.respondent,
        )

        SubmissionAnswer.objects.create(
            submission=submission,
            question=question,
            answer_option=option,
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                SubmissionAnswer.objects.create(
                    submission=submission,
                    question=question,
                    answer_option=option,
                )

    def test_question_template_basic_fields(self) -> None:
        template = QuestionTemplate.objects.create(
            text="Template question",
        )

        self.assertEqual(template.text, "Template question")

    def test_create_question_from_template(self) -> None:
        survey = Survey.objects.create(
            title="Template survey",
            author=self.author,
        )
        template = QuestionTemplate.objects.create(
            text="How old are you?",
        )

        question = Question.objects.create(
            survey=survey,
            text=template.text,
            order=1,
        )

        self.assertEqual(question.text, template.text)
        self.assertEqual(question.survey, survey)

