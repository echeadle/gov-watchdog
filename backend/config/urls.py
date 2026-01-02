"""
URL configuration for Gov Watchdog project.
"""

from django.urls import include, path

urlpatterns = [
    path("api/v1/members/", include("members.urls")),
    path("api/v1/bills/", include("bills.urls")),
    path("api/v1/votes/", include("votes.urls")),
    path("api/v1/agent/", include("agent.urls")),
]

# Health check endpoint
from django.http import JsonResponse


async def health_check(request):
    """Simple health check endpoint."""
    return JsonResponse({"status": "healthy"})


urlpatterns += [
    path("health/", health_check, name="health_check"),
]
