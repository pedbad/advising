from django.urls import path

from . import views

app_name = "notes"

urlpatterns = [
    path("mine/", views.my_notes, name="my_notes"),
    path("students/", views.student_selector, name="student_selector"),
    path("students/<int:student_id>/", views.student_notes, name="student_notes"),
]
