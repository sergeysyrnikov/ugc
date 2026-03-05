from django.contrib import admin

from .models import (
    Answer,
    Question,
    QuestionTemplate,
    Submission,
    SubmissionAnswer,
    Survey,
)


@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "author", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("title", "description")
    raw_id_fields = ("author",)
    date_hierarchy = "created_at"


@admin.register(QuestionTemplate)
class QuestionTemplateAdmin(admin.ModelAdmin):
    list_display = ("id", "short_text")
    search_fields = ("text",)

    def short_text(self, obj: QuestionTemplate) -> str:
        return str(obj)

    short_text.short_description = "Question"


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "survey", "order")
    list_filter = ("survey",)
    search_fields = ("text",)
    raw_id_fields = ("survey",)


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ("id", "question", "order")
    list_filter = ("question",)
    search_fields = ("text",)
    raw_id_fields = ("question",)


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ("id", "survey", "user", "started_at", "finished_at")
    list_filter = ("started_at", "finished_at")
    raw_id_fields = ("survey", "user")
    date_hierarchy = "started_at"


@admin.register(SubmissionAnswer)
class SubmissionAnswerAdmin(admin.ModelAdmin):
    list_display = ("id", "submission", "question", "answer", "answered_at")
    list_filter = ("answered_at",)
    raw_id_fields = ("submission", "question", "answer")
    date_hierarchy = "answered_at"
