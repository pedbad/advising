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
    # Availability list view
    path("list/", views.availability_list, name="availability_list"),
    # Upcoming availability list (admin only)
    path("upcoming/", views.upcoming_availability_list, name="upcoming_availability"),
    # All bookings (admin only)
    path("all-bookings/", views.all_bookings_view, name="all_bookings"),
    # Date detail view
    path("date/<int:year>/<int:month>/<int:day>/", views.date_detail_view, name="date_detail"),
    # AJAX endpoint for saving availability
    path("api/save-availability/", views.save_availability, name="save_availability"),
]
