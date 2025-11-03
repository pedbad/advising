"""
Models for the questionnaire app.
"""

from django.db import models


class Questionnaire(models.Model):
    """
    Questionnaire for students to complete when they first register.
    Students can submit multiple versions (allows updates/resubmissions).
    """

    student_profile = models.ForeignKey(
        "profiles.StudentProfile",
        on_delete=models.CASCADE,
        related_name="questionnaires",
        help_text="The student profile this questionnaire belongs to",
    )

    # Basic Information
    faculty_department = models.CharField(
        max_length=150,
        blank=False,
        null=False,
        help_text="Enter your faculty or department. If none, type 'External'.",
    )

    mother_tongue = models.CharField(
        max_length=100,
        blank=False,
        null=False,
        help_text=(
            "Enter your first/native language. " "If multilingual, list them separated by commas."
        ),
    )

    UNIVERSITY_STATUS_CHOICES = [
        ("undergrad_first", "Undergraduate student (1st Year)"),
        ("undergrad_other", "Undergraduate student (Other Years)"),
        ("mphil", "MPhil student"),
        ("phd_first", "PhD student (1st Year)"),
        ("phd_other", "PhD student (Other Years)"),
        ("postdoc", "Post-doctoral research"),
        ("academic_staff", "Academic staff / Lecturer"),
        ("support_staff", "Support staff"),
        ("fee_paying", "Fee-paying member"),
        ("academic_visitor", "Academic visitor"),
        ("other", "Other"),
    ]

    university_status = models.CharField(
        max_length=50,
        choices=UNIVERSITY_STATUS_CHOICES,
        blank=False,
        null=False,
        help_text="Select your current university status.",
    )

    # Language Learning - Mandatory
    LANGUAGE_PROFICIENCY_CHOICES = [
        ("beginner", "Beginner"),
        ("intermediate", "Intermediate"),
        ("advanced", "Advanced"),
    ]

    language_mandatory_name = models.CharField(
        max_length=100,
        blank=False,
        null=False,
        help_text="Specify the main language you wish to learn or improve.",
    )

    language_mandatory_proficiency = models.CharField(
        max_length=20,
        choices=LANGUAGE_PROFICIENCY_CHOICES,
        blank=False,
        null=False,
        help_text="Select your current proficiency level for this language.",
    )

    language_mandatory_goals = models.JSONField(
        blank=False,
        null=False,
        help_text="List of learning/development goals selected for this language.",
    )

    # Language Learning - Optional
    language_optional_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Specify an additional language you wish to learn or improve (optional).",
    )

    language_optional_proficiency = models.CharField(
        max_length=20,
        choices=LANGUAGE_PROFICIENCY_CHOICES,
        blank=True,
        null=True,
        help_text="Select your current proficiency level for this additional language.",
    )

    language_optional_goals = models.JSONField(
        blank=True,
        null=True,
        help_text="List of learning/development goals selected for this additional language.",
    )

    # Learning Details
    aspects_to_improve = models.TextField(
        max_length=2000,
        blank=False,
        null=False,
        help_text="What specific aspects of the language(s) would you like to learn or improve?",
    )

    activities_you_can_manage = models.TextField(
        max_length=2000,
        blank=False,
        null=False,
        help_text="List the activities you can manage in the language(s)",
    )

    hours_per_week = models.CharField(
        max_length=300,
        blank=False,
        null=False,
        help_text="Roughly how many hours per week will you devote to language learning?",
    )

    other_languages_studied = models.TextField(
        max_length=1000,
        blank=True,
        null=True,
        help_text="List any other languages you have previously studied (optional).",
    )

    additional_comments = models.TextField(
        max_length=2000,
        blank=True,
        null=True,
        help_text="Any final comments you'd like to share with us (optional).",
    )

    # Status and Timestamps
    completed = models.BooleanField(
        default=False, help_text="Whether this questionnaire has been completed and submitted"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        status = "Completed" if self.completed else "Incomplete"
        date_str = self.created_at.strftime("%Y-%m-%d")
        return f"Questionnaire for {self.student_profile.user.email} ({status}) - {date_str}"

    class Meta:
        verbose_name = "Questionnaire"
        verbose_name_plural = "Questionnaires"
        ordering = ["-created_at"]
