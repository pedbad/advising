# src/config/urls.py
from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls", namespace="core")),
    path("users/", include("users.urls", namespace="users")),
    path("booking/", include("booking.urls", namespace="booking")),
    path("availability/", include("availability.urls", namespace="availability")),
    path("profiles/", include("profiles.urls", namespace="profiles")),
    path("questionnaire/", include("questionnaire.urls", namespace="questionnaire")),
    path("notes/", include("notes.urls", namespace="notes")),
]

if settings.DEBUG:
    urlpatterns += [path("__reload__/", include("django_browser_reload.urls"))]
