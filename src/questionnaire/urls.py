"""
URL configuration for the questionnaire app.
"""

from django.urls import path

from . import views

app_name = "questionnaire"

urlpatterns = [
    # Questionnaire URLs
    path("", views.questionnaire_view, name="questionnaire"),
    path("student/<int:student_id>/", views.questionnaire_view, name="view_student_questionnaire"),
]
