from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    REGISTRY,
    generate_latest,
)


UGC_SURVEY_REQUESTS_TOTAL: Counter = Counter(
    "ugc_survey_requests_total",
    "Total number of survey next-question API requests.",
)

HTTP_REQUESTS_TOTAL: Counter = Counter(
    "ugc_http_requests_total",
    "Total number of HTTP requests processed by Django.",
    ["method", "path", "status_code"],
)

HTTP_REQUEST_LATENCY_SECONDS: Histogram = Histogram(
    "ugc_http_request_latency_seconds",
    "HTTP request latency in seconds.",
    ["method", "path", "status_code"],
)


def metrics_view(request: HttpRequest) -> HttpResponse:
    """Expose Prometheus metrics for the Django application."""
    metrics_payload = generate_latest(REGISTRY)
    return HttpResponse(metrics_payload, content_type=CONTENT_TYPE_LATEST)


