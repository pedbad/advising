"""
Models for the booking app.
"""

from django.conf import settings
from django.db import models


class Booking(models.Model):
    """
    Represents a student's booking of a specific availability slot.

    A booking links a student to a teacher's availability slot.
    """

    availability = models.OneToOneField(
        "availability.Availability",
        on_delete=models.CASCADE,
        related_name="booking",
        help_text="The availability slot being booked",
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bookings",
        limit_choices_to={"role": "student"},
    )
    message = models.TextField(
        blank=True,
        default="",
        help_text="Optional message from student to teacher",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["availability__date", "availability__start_time"]
        indexes = [
            models.Index(fields=["student", "availability"]),
        ]
        db_table = "availability_booking"

    def __str__(self):
        return f"{self.student.email} - {self.availability}"
