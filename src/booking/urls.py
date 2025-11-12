from django.urls import path

from . import views

app_name = "booking"

urlpatterns = [
    path("student/book-meeting/", views.book_meeting, name="book_meeting"),
    path("student/cancel-booking/<int:booking_id>/", views.cancel_booking, name="cancel_booking"),
    path("event/<int:booking_id>/ics/", views.booking_ics, name="booking_ics"),
]
