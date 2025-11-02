"""
URL configuration for the availability app.
"""

from django.urls import path

from . import views

app_name = "availability"

urlpatterns = [
    # Calendar views
    path("calendar/", views.calendar_view, name="calendar"),
    path("calendar/<int:year>/<int:month>/", views.calendar_view, name="calendar_month"),
    # Date detail view
    path("date/<int:year>/<int:month>/<int:day>/", views.date_detail_view, name="date_detail"),
]
