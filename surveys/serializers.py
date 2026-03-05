from rest_framework import serializers

from surveys.models import Answer, Question


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

