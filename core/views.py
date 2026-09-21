"""
Core project views.

Service-level endpoints (health checks).
"""

from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse
from django.views import View


def _check_database():
    """Verify database connectivity with a trivial query."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        cursor.fetchone()
    return "ok"


def _check_cache():
    """Verify cache backend with a round-trip write."""
    cache.set("healthcheck", "ok", timeout=10)
    if cache.get("healthcheck") != "ok":
        raise ConnectionError("cache round-trip mismatch")
    return "ok"


class HealthView(View):
    """
    Service health endpoint.

    Returns 200 when database and cache are reachable,
    503 otherwise. Used by load balancers and monitors.
    """

    def get(self, request):
        """Report database and cache connectivity."""
        checks = {}
        for name, check in (("db", _check_database), ("cache", _check_cache)):
            try:
                checks[name] = check()
            except Exception as exc:
                checks[name] = f"error: {exc}"

        healthy = all(status == "ok" for status in checks.values())
        payload = {"status": "healthy" if healthy else "unhealthy", **checks}
        return JsonResponse(payload, status=200 if healthy else 503)
