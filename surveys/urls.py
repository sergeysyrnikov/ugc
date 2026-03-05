from django.urls import path

from surveys.views import NextQuestionAPIView

urlpatterns = [
    path(
        "<int:survey_id>/submissions/<int:submission_id>/next-question/",
        NextQuestionAPIView.as_view(),
        name="survey-next-question",
    ),
]

