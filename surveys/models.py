from __future__ import annotations

from django.conf import settings
from django.db import models


class TimeStampedModel(models.Model):
    """Abstract base model with created/updated timestamps."""

    updated_at: models.DateTimeField = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated at",
    )
    created_at: models.DateTimeField = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created at",
    )

    class Meta:
        abstract = True


class SurveyStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PUBLISHED = "published", "Published"


class Survey(TimeStampedModel):
    """Represents a survey created by a user."""

    title: models.CharField = models.CharField(
        max_length=255,
        verbose_name="Title",
    )
    description: models.TextField = models.TextField(
        blank=True,
        verbose_name="Description",
    )
    author: models.ForeignKey = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="surveys",
        verbose_name="Author",
    )
    status: models.CharField = models.CharField(
        max_length=16,
        choices=SurveyStatus.choices,
        default=SurveyStatus.DRAFT,
        db_index=True,
        verbose_name="Status",
    )

    class Meta:
        verbose_name = "Survey"
        verbose_name_plural = "Surveys"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title


class QuestionTemplate(TimeStampedModel):
    """Represents a reusable question template."""

    text: models.TextField = models.TextField(
        max_length=512,
        verbose_name="Question text",
    )

    class Meta:
        verbose_name = "Question template"
        verbose_name_plural = "Question templates"
        ordering = ["id"]

    def __str__(self) -> str:
        return self.text if len(self.text) <= 50 else f"{self.text[:47]}..."


class Question(TimeStampedModel):
    """Represents a question inside a survey."""

    survey: models.ForeignKey = models.ForeignKey(
        Survey,
        on_delete=models.CASCADE,
        related_name="questions",
        verbose_name="Survey",
    )
    text: models.TextField = models.TextField(
        max_length=512,
        verbose_name="Question text",
    )
    order: models.PositiveSmallIntegerField = models.PositiveSmallIntegerField(
        verbose_name="Order",
    )

    class Meta:
        verbose_name = "Question"
        verbose_name_plural = "Questions"
        ordering = ["order", "id"]
        indexes = [
            models.Index(
                fields=["survey", "order"],
                name="question_survey_order_idx",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(order__gte=1, order__lte=30),
                name="question_order_between_1_and_30",
            ),
        ]

    def __str__(self) -> str:
        return self.text if len(self.text) <= 50 else f"{self.text[:47]}..."


class Answer(TimeStampedModel):
    """Represents an answer for a question."""

    question: models.ForeignKey = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="answers",
        verbose_name="Question",
    )
    text: models.CharField = models.CharField(
        max_length=512,
        verbose_name="Answer text",
    )
    order: models.PositiveSmallIntegerField = models.PositiveSmallIntegerField(
        verbose_name="Order",
    )

    class Meta:
        verbose_name = "Answer"
        verbose_name_plural = "Answers"
        ordering = ["order", "id"]
        indexes = [
            models.Index(
                fields=["question", "order"],
                name="answer_question_order_idx",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(order__gte=1, order__lte=15),
                name="answer_order_between_1_and_15",
            ),
        ]

    def __str__(self) -> str:
        return self.text if len(self.text) <= 50 else f"{self.text[:47]}..."


class Submission(TimeStampedModel):
    """Represents a single survey submission by a user."""

    survey: models.ForeignKey = models.ForeignKey(
        Survey,
        on_delete=models.CASCADE,
        related_name="submissions",
        verbose_name="Survey",
    )
    user: models.ForeignKey = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="submissions",
        verbose_name="User",
    )
    started_at: models.DateTimeField = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Started at",
    )
    finished_at: models.DateTimeField = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Finished at",
    )

    class Meta:
        verbose_name = "Submission"
        verbose_name_plural = "Submissions"

    def __str__(self) -> str:
        return f"Submission #{self.pk} for {self.survey_id}"


class SubmissionAnswer(TimeStampedModel):
    """Represents a single answer within a submission."""

    submission: models.ForeignKey = models.ForeignKey(
        Submission,
        on_delete=models.CASCADE,
        related_name="answers",
        verbose_name="Submission",
    )
    question: models.ForeignKey = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="submission_answers",
        verbose_name="Question",
    )
    answer: models.ForeignKey = models.ForeignKey(
        Answer,
        on_delete=models.CASCADE,
        related_name="submission_answers",
        verbose_name="Answer",
    )
    free_text: models.TextField = models.TextField(
        blank=True,
        verbose_name="Free text",
        help_text="Optional user-entered free text answer.",
    )
    answered_at: models.DateTimeField = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Answered at",
    )

    class Meta:
        verbose_name = "Submission answer"
        verbose_name_plural = "Submission answers"
        constraints = [
            models.UniqueConstraint(
                fields=["submission", "question"],
                name="submission_question_unique",
            ),
        ]

    def __str__(self) -> str:
        return f"Answer #{self.pk} for submission {self.submission_id}"
