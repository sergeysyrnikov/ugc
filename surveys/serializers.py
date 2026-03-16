from __future__ import annotations

from typing import Any, ClassVar

from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from surveys.models import (
    Answer,
    Question,
    QuestionTemplate,
    Submission,
    SubmissionAnswer,
    Survey,
)

User = get_user_model()


# --- Nested serializers (for next-question API and read-only nesting) ---


class AnswerSerializer(serializers.ModelSerializer):
    """Serializer for answer options within a question."""

    class Meta:
        model = Answer
        fields = [
            "id",
            "text",
            "order",
        ]


class QuestionSerializer(serializers.ModelSerializer):
    """Serializer for survey questions with nested answers."""

    answers = AnswerSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = [
            "id",
            "text",
            "order",
            "answers",
        ]


class AnswerNestedWritableSerializer(serializers.ModelSerializer):
    """Writable nested serializer for answer options (create/update within question)."""

    class Meta:
        model = Answer
        fields = ["id", "text", "order"]
        read_only_fields = ["id"]

    def validate_order(self, value: int) -> int:
        if value < 1 or value > 15:
            raise serializers.ValidationError("Order must be between 1 and 15.")
        return value


class QuestionNestedWritableSerializer(serializers.ModelSerializer):
    """Writable nested serializer for questions with nested answers (create/update within survey)."""

    answers = AnswerNestedWritableSerializer(many=True)

    class Meta:
        model = Question
        fields = ["id", "text", "order", "answers"]
        read_only_fields = ["id"]

    def validate_order(self, value: int) -> int:
        if value < 1 or value > 30:
            raise serializers.ValidationError("Order must be between 1 and 30.")
        return value


# --- CRUD serializers (staff-only API) ---


class SurveyListRetrieveSerializer(serializers.ModelSerializer):
    """CRUD serializer for Survey."""

    questions: ClassVar[Any] = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Survey
        fields = [
            "id",
            "title",
            "description",
            "author",
            "status",
            "created_at",
            "updated_at",
            "questions",
        ]
        read_only_fields = ["created_at", "updated_at"]
        extra_kwargs = {"author": {"required": False}}


class SurveyWithQuestionsSerializer(SurveyListRetrieveSerializer):
    """Survey serializer with nested questions and answers (create/update/read)."""

    questions: ClassVar[Any] = QuestionNestedWritableSerializer(
        many=True, required=False, default=list
    )

    def create(self, validated_data: dict) -> Survey:
        questions_data = validated_data.pop("questions", [])
        if validated_data.get("author") is None:
            request = self.context.get("request")
            if request and getattr(request, "user", None):
                validated_data["author"] = request.user
        survey = Survey.objects.create(**validated_data)
        self._create_questions(survey, questions_data)
        return survey

    def update(self, instance: Survey, validated_data: dict) -> Survey:
        questions_data = validated_data.pop("questions", None)
        deleted_question_ids = validated_data.pop("deletedQuestionIds", [])
        deleted_answer_ids = validated_data.pop("deletedAnswerIds", [])
        if deleted_question_ids:
            instance.questions.filter(id__in=deleted_question_ids).delete()
            instance.refresh_from_db(fields=["questions"])
        if deleted_answer_ids:
            for question in instance.questions.all():
                question.answers.filter(id__in=deleted_answer_ids).delete()
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if questions_data is not None:
            self._update_questions(instance, questions_data)
        return instance

    def _create_questions(self, survey: Survey, questions_data: list[dict]) -> None:
        for q_data in questions_data:
            answers_data = q_data.pop("answers", [])
            q_data.pop("id", None)
            question = Question.objects.create(survey=survey, **q_data)
            if answers_data:
                answers = [
                    Answer(question=question, text=a["text"], order=a["order"])
                    for a in answers_data
                ]
                Answer.objects.bulk_create(answers)

    def _update_questions(self, survey: Survey, questions_data: list[dict]) -> None:
        payload_ids = {q["id"] for q in questions_data if q.get("id")}
        survey.questions.exclude(id__in=payload_ids).delete()
        for q_data in questions_data:
            answers_data = q_data.pop("answers", [])
            q_id = q_data.pop("id", None)
            if q_id and survey.questions.filter(id=q_id).exists():
                question = survey.questions.get(id=q_id)
                for attr, value in q_data.items():
                    setattr(question, attr, value)
                question.save()
                self._update_answers(question, answers_data)
            else:
                question = Question.objects.create(survey=survey, **q_data)
                if answers_data:
                    answers = [
                        Answer(question=question, text=a["text"], order=a["order"])
                        for a in answers_data
                    ]
                    Answer.objects.bulk_create(answers)

    def _update_answers(self, question: Question, answers_data: list[dict]) -> None:
        payload_ids = {a["id"] for a in answers_data if a.get("id")}
        question.answers.exclude(id__in=payload_ids).delete()
        to_create: list[Answer] = []
        for a_data in answers_data:
            a_id = a_data.pop("id", None)
            if a_id and question.answers.filter(id=a_id).exists():
                answer = question.answers.get(id=a_id)
                for attr, value in a_data.items():
                    setattr(answer, attr, value)
                answer.save()
            else:
                to_create.append(
                    Answer(
                        question=question, text=a_data["text"], order=a_data["order"]
                    )
                )
        if to_create:
            Answer.objects.bulk_create(to_create)


class QuestionTemplateSerializer(serializers.ModelSerializer):
    """CRUD serializer for QuestionTemplate."""

    class Meta:
        model = QuestionTemplate
        fields = [
            "id",
            "text",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class QuestionCrudSerializer(serializers.ModelSerializer):
    """CRUD serializer for Question (with optional nested answers read-only)."""

    answers = AnswerSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = [
            "id",
            "survey",
            "text",
            "order",
            "answers",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def validate_order(self, value: int) -> int:
        if value < 1 or value > 30:
            raise serializers.ValidationError("Order must be between 1 and 30.")
        return value


class AnswerCrudSerializer(serializers.ModelSerializer):
    """CRUD serializer for Answer."""

    class Meta:
        model = Answer
        fields = [
            "id",
            "question",
            "text",
            "order",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def validate_order(self, value: int) -> int:
        if value < 1 or value > 15:
            raise serializers.ValidationError("Order must be between 1 and 15.")
        return value


class SubmissionSerializer(serializers.ModelSerializer):
    """CRUD serializer for Submission."""

    class Meta:
        model = Submission
        fields = [
            "id",
            "survey",
            "user",
            "started_at",
            "finished_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class SubmissionAnswerSerializer(serializers.ModelSerializer):
    """CRUD serializer for SubmissionAnswer."""

    class Meta:
        model = SubmissionAnswer
        fields = [
            "id",
            "submission",
            "question",
            "answer",
            "free_text",
            "answered_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "answered_at"]
        validators = [
            UniqueTogetherValidator(
                queryset=SubmissionAnswer.objects.all(),
                fields=("submission", "question"),
                message="This submission already has an answer for this question.",
            ),
        ]
