from __future__ import annotations

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from booking.models import Booking
from notes.models import NoteComment, StudentNote
from notifications import emails


@receiver(post_save, sender=Booking)
def booking_created(sender, instance: Booking, created: bool, **kwargs):
    if not created:
        return
    emails.send_booking_confirmation(booking=instance)


@receiver(pre_delete, sender=Booking)
def booking_deleted(sender, instance: Booking, **kwargs):
    reason = getattr(instance, "cancellation_message", "")
    emails.send_booking_cancellation(booking=instance, cancellation_message=reason)


@receiver(post_save, sender=StudentNote)
def note_created(sender, instance: StudentNote, created: bool, **kwargs):
    if not created:
        return
    emails.send_student_note_notification(note=instance)
    emails.send_student_note_confirmation(note=instance)


@receiver(post_save, sender=NoteComment)
def note_comment_created(sender, instance: NoteComment, created: bool, **kwargs):
    if not created:
        return
    emails.send_note_comment_notification(comment=instance)
    emails.send_note_comment_confirmation(comment=instance)
