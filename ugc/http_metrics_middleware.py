from __future__ import annotations

import time
from typing import Callable

from django.http import HttpRequest, HttpResponse

from ugc.metrics import HTTP_REQUEST_LATENCY_SECONDS, HTTP_REQUESTS_TOTAL


class HttpMetricsMiddleware:
    """Middleware that records HTTP request metrics for Prometheus."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        start_time = time.perf_counter()
        method = request.method
        path = request.path
        status_code = "500"

        try:
            response = self.get_response(request)
            status_code = str(response.status_code)
            return response
        finally:
            elapsed = time.perf_counter() - start_time
            print(f"elapsed: {elapsed}")
            print(f"method: {method}")
            print(f"path: {path}")
            print(f"status_code: {status_code}")
            HTTP_REQUESTS_TOTAL.labels(
                method=method,
                path=path,
                status_code=status_code,
            ).inc()
            HTTP_REQUEST_LATENCY_SECONDS.labels(
                method=method,
                path=path,
                status_code=status_code,
            ).observe(elapsed)
