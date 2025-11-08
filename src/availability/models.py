"""
Models for the availability app.
"""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models

User = get_user_model()


class Availability(models.Model):
    """
    Represents a teacher's availability for a specific time slot on a specific date.

    Each availability slot is 30 minutes long (two consecutive 15-minute slots).
    """

    class MeetingType(models.TextChoices):
        ONLINE = "online", "Online"
        IN_PERSON = "in_person", "In-person"
        BOTH = "both", "Both (Online + In-person)"

    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="availabilities",
        limit_choices_to={"role": "teacher"},
    )
    date = models.DateField(db_index=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    meeting_type = models.CharField(
        max_length=20,
        choices=MeetingType.choices,
        default=MeetingType.BOTH,
    )
    message = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Optional short message or note for this time slot (max 200 characters)",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Availabilities"
        unique_together = [["teacher", "date", "start_time"]]
        ordering = ["date", "start_time"]
        indexes = [
            models.Index(fields=["teacher", "date"]),
        ]

    def __str__(self):
        return (
            f"{self.teacher.email} - {self.date} "
            f"{self.start_time}-{self.end_time} "
            f"({self.get_meeting_type_display()})"
        )

    def clean(self):
        """Validate that the time slot is exactly 30 minutes."""
        if self.start_time and self.end_time:
            # Calculate duration
            from datetime import datetime

            start_dt = datetime.combine(self.date, self.start_time)
            end_dt = datetime.combine(self.date, self.end_time)
            duration = (end_dt - start_dt).total_seconds() / 60

            meeting_duration = settings.AVAILABILITY_SETTINGS.get("MEETING_DURATION", 30)
            if duration != meeting_duration:
                raise ValidationError(f"Time slot must be exactly {meeting_duration} minutes long.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
