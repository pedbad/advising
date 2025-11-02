"""
Admin configuration for availability app.
"""

from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Availability


@admin.register(Availability)
class AvailabilityAdmin(ModelAdmin):
    """Admin interface for Availability model."""

    list_display = ["teacher", "date", "start_time", "end_time", "meeting_type", "created_at"]
    list_filter = ["meeting_type", "date", "teacher"]
    search_fields = ["teacher__email", "teacher__first_name", "teacher__last_name"]
    date_hierarchy = "date"
    ordering = ["-date", "start_time"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (
            "Availability Details",
            {
                "fields": ("teacher", "date", "start_time", "end_time", "meeting_type"),
            },
        ),
        (
            "Metadata",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )
