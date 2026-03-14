from __future__ import annotations

from django.db import models
from djangorestframework_mcp.decorators import mcp_viewset
from rest_framework import permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from surveys.models import (
    Answer,
    Question,
    QuestionTemplate,
    Submission,
    SubmissionAnswer,
    Survey,
)
from surveys.serializers import (
    AnswerCrudSerializer,
    QuestionCrudSerializer,
    QuestionSerializer,
    QuestionTemplateSerializer,
    SubmissionAnswerSerializer,
    SubmissionSerializer,
    SurveySerializer,
)
from ugc.metrics import UGC_SURVEY_REQUESTS_TOTAL


class SurveyListPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100
    max_page_number = 5000

    def paginate_queryset(self, queryset, request, view=None):
        page_number = request.query_params.get(self.page_query_param, 1)
        try:
            page_number = int(page_number)
        except (TypeError, ValueError):
            page_number = 1
        if page_number > self.max_page_number:
            raise ValidationError(
                detail={
                    "detail": (
                        f"Page number {page_number} exceeds maximum {self.max_page_number}. "
                        "Use a lower page number or filter the list."
                    )
                },
                code="page_too_high",
            )
        return super().paginate_queryset(queryset, request, view=view)


@mcp_viewset()
class SurveyViewSet(ModelViewSet[Survey]):
    """CRUD for surveys. List and retrieve: any authenticated user; create/update/delete: staff only."""

    def get_permissions(self) -> list[permissions.BasePermission]:
        if self.action in ["list", "retrieve"]:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), permissions.IsAdminUser()]

    def get_queryset(self) -> models.QuerySet[Survey]:
        return Survey.objects.all().order_by("-id").select_related("author")

    serializer_class = SurveySerializer
    pagination_class = SurveyListPagination


@mcp_viewset()
class QuestionTemplateViewSet(ModelViewSet[QuestionTemplate]):
    """CRUD for question templates. Staff only."""

    queryset = QuestionTemplate.objects.all().order_by("id")
    serializer_class = QuestionTemplateSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]


@mcp_viewset()
class QuestionViewSet(ModelViewSet[Question]):
    """CRUD for questions. Staff only."""

    queryset = Question.objects.all().order_by("order", "id")
    serializer_class = QuestionCrudSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]


@mcp_viewset()
class AnswerViewSet(ModelViewSet[Answer]):
    """CRUD for answers. Staff only."""

    queryset = Answer.objects.all().order_by("order", "id")
    serializer_class = AnswerCrudSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]


@mcp_viewset()
class SubmissionViewSet(ModelViewSet[Submission]):
    """CRUD for submissions. Staff only."""

    queryset = Submission.objects.all().order_by("-created_at")
    serializer_class = SubmissionSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]


@mcp_viewset()
class SubmissionAnswerViewSet(ModelViewSet[SubmissionAnswer]):
    """CRUD for submission answers. Staff only."""

    queryset = SubmissionAnswer.objects.all().order_by("id")
    serializer_class = SubmissionAnswerSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]


class NextQuestionAPIView(APIView):
    """Return the next unanswered question for a given survey submission."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, survey_id: int, submission_id: int) -> Response:
        UGC_SURVEY_REQUESTS_TOTAL.inc()
        try:
            survey = Survey.objects.get(pk=survey_id)
        except Survey.DoesNotExist:
            return Response(
                data={"detail": "Survey not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            submission = Submission.objects.get(pk=submission_id)
        except Submission.DoesNotExist:
            return Response(
                data={"detail": "Submission not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if submission.survey_id != survey.id:
            return Response(
                data={"detail": "Submission does not belong to this survey."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        answered_question_ids = SubmissionAnswer.objects.filter(
            submission=submission,
        ).values_list("question_id", flat=True)

        queryset = (
            Question.objects.filter(survey=survey)
            .exclude(id__in=answered_question_ids)
            .order_by("order", "id")
            .prefetch_related("answers")
        )
        next_question = queryset.first()

        if next_question is None:
            return Response(
                data={
                    "question": None,
                    "is_finished": True,
                },
                status=status.HTTP_200_OK,
            )

        serialized_question = QuestionSerializer(next_question)
        return Response(
            data={
                "question": serialized_question.data,
                "is_finished": False,
            },
            status=status.HTTP_200_OK,
        )
