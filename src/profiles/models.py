"""
Models for the profiles app.
"""

from django.conf import settings
from django.db import models


class StudentProfile(models.Model):
    """
    Profile for students. Created automatically when a student user is registered.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student_profile",
        limit_choices_to={"role": "student"},
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Student Profile: {self.user.email}"

    def has_completed_questionnaire(self):
        """Check if the student has completed at least one questionnaire."""
        return self.questionnaires.filter(completed=True).exists()

    class Meta:
        verbose_name = "Student Profile"
        verbose_name_plural = "Student Profiles"
