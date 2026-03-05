from __future__ import annotations

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


# --- CRUD serializers (staff-only API) ---


class SurveySerializer(serializers.ModelSerializer):
    """CRUD serializer for Survey."""

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
        ]
        read_only_fields = ["created_at", "updated_at"]
        extra_kwargs = {"author": {"required": False}}

    def create(self, validated_data: dict) -> Survey:
        if validated_data.get("author") is None:
            request = self.context.get("request")
            if request and getattr(request, "user", None):
                validated_data["author"] = request.user
        return super().create(validated_data)


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
