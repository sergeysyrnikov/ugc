from django.urls import include, path
from rest_framework.routers import DefaultRouter

from surveys.views import (
    AnswerViewSet,
    NextQuestionAPIView,
    QuestionTemplateViewSet,
    QuestionViewSet,
    SubmissionAnswerViewSet,
    SubmissionViewSet,
    SurveyViewSet,
)

router = DefaultRouter()
# Register with non-empty prefixes first so "^<pk>/" does not catch them.
router.register(
    "question-templates", QuestionTemplateViewSet, basename="questiontemplate"
)
router.register("questions", QuestionViewSet, basename="question")
router.register("answers", AnswerViewSet, basename="answer")
router.register("submissions", SubmissionViewSet, basename="submission")
router.register(
    "submission-answers", SubmissionAnswerViewSet, basename="submissionanswer"
)
router.register("", SurveyViewSet, basename="survey")

urlpatterns = [
    path(
        "<int:survey_id>/submissions/<int:submission_id>/next-question/",
        NextQuestionAPIView.as_view(),
        name="survey-next-question",
    ),
    path("", include(router.urls)),
]
