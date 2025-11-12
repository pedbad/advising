from django.conf import settings
from django.db import models


class StudentNote(models.Model):
    """A root note addressed to a specific student profile."""

    student_profile = models.ForeignKey(
        "profiles.StudentProfile",
        on_delete=models.CASCADE,
        related_name="notes",
    )
    title = models.CharField(max_length=200, blank=True)
    body = models.TextField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student_notes_created",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="student_notes_updated",
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-last_activity_at", "-created_at"]
        indexes = [
            models.Index(fields=["student_profile", "created_at"]),
        ]

    def __str__(self):
        base = self.title or self.body[:40]
        return f"Note for {self.student_profile.user.email}: {base}".strip()


class NoteComment(models.Model):
    """Threaded comments under a student note."""

    note = models.ForeignKey(
        StudentNote,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="note_comments",
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment by {self.author.email} on note {self.note_id}"
