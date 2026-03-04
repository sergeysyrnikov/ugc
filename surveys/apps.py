from django.apps import AppConfig


class SurveysConfig(AppConfig):
    """App configuration for surveys."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "surveys"
    verbose_name = "Surveys"

