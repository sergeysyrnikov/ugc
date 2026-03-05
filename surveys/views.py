from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from surveys.models import Question, Submission, SubmissionAnswer, Survey
from surveys.serializers import QuestionSerializer


class NextQuestionAPIView(APIView):
    """Return the next unanswered question for a given survey submission."""

    permission_classes = [IsAuthenticated]

    def get(self, request, survey_id: int, submission_id: int) -> Response:
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
