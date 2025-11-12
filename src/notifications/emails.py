"""Notification email helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from users.utils import get_domain_and_scheme


@dataclass
class Recipient:
    email: str
    name: str | None = None

    def display_name(self) -> str:
        if self.name:
            return self.name
        return self.email


def _send_email(*, subject: str, template: str, context: dict, to: Iterable[Recipient]):
    """Render a notification template (txt + optional html) and send."""
    if not to:
        return

    context = {"SITE_NAME": getattr(settings, "SITE_NAME", "Advising"), **context}
    recipients = [recipient for recipient in to if recipient.email]
    for recipient in recipients:
        txt_body = render_to_string(f"notifications/email/{template}.txt", context)
        html_path = f"notifications/email/{template}.html"
        try:
            html_body = render_to_string(html_path, context)
        except Exception:
            html_body = None

        msg = EmailMultiAlternatives(
            subject=subject,
            body=txt_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient.email],
        )
        if html_body:
            msg.attach_alternative(html_body, "text/html")
        msg.send()


def admin_recipients() -> list[Recipient]:
    User = get_user_model()
    admins = User.objects.filter(role=getattr(User.Roles, "ADMIN", "admin")).only(
        "email", "first_name", "last_name"
    )
    recipients: list[Recipient] = []
    for admin in admins:
        if admin.email:
            recipients.append(Recipient(email=admin.email, name=admin.get_full_name()))
    return recipients


def send_booking_confirmation(*, booking):
    domain, use_https = get_domain_and_scheme()
    context = {
        "booking": booking,
        "student": booking.student,
        "advisor": booking.availability.teacher,
        "slot": booking.availability,
        "domain": domain,
        "protocol": "https" if use_https else "http",
    }
    recipients = [
        Recipient(email=booking.student.email, name=booking.student.get_full_name()),
        Recipient(email=booking.availability.teacher.email, name=booking.availability.teacher.get_full_name()),
    ]
    recipients.extend(admin_recipients())
    _send_email(
        subject="Booking confirmed",
        template="booking_confirmation",
        context=context,
        to=recipients,
    )


def send_booking_cancellation(*, booking):
    domain, use_https = get_domain_and_scheme()
    context = {
        "booking": booking,
        "student": booking.student,
        "advisor": booking.availability.teacher,
        "slot": booking.availability,
        "domain": domain,
        "protocol": "https" if use_https else "http",
    }
    recipients = [
        Recipient(email=booking.student.email, name=booking.student.get_full_name()),
        Recipient(email=booking.availability.teacher.email, name=booking.availability.teacher.get_full_name()),
    ]
    recipients.extend(admin_recipients())
    _send_email(
        subject="Booking cancelled",
        template="booking_cancellation",
        context=context,
        to=recipients,
    )


def send_student_note_notification(*, note):
    domain, use_https = get_domain_and_scheme()
    context = {
        "note": note,
        "student": note.student_profile.user,
        "advisor": note.created_by,
        "domain": domain,
        "protocol": "https" if use_https else "http",
    }
    recipients = [Recipient(email=note.student_profile.user.email, name=note.student_profile.user.get_full_name())]
    _send_email(
        subject="New advisor note",
        template="student_note",
        context=context,
        to=recipients,
    )


def send_student_note_confirmation(*, note):
    domain, use_https = get_domain_and_scheme()
    context = {
        "note": note,
        "student": note.student_profile.user,
        "advisor": note.created_by,
        "domain": domain,
        "protocol": "https" if use_https else "http",
    }
    recipients = [Recipient(email=note.created_by.email, name=note.created_by.get_full_name())]
    _send_email(
        subject="Your note was sent",
        template="note_confirmation",
        context=context,
        to=recipients,
    )


def send_note_comment_notification(*, comment):
    domain, use_https = get_domain_and_scheme()
    context = {
        "comment": comment,
        "note": comment.note,
        "student": comment.note.student_profile.user,
        "advisor": comment.author,
        "domain": domain,
        "protocol": "https" if use_https else "http",
    }
    recipients = [Recipient(email=comment.note.student_profile.user.email, name=comment.note.student_profile.user.get_full_name())]
    _send_email(
        subject="New comment on your note",
        template="note_comment",
        context=context,
        to=recipients,
    )


def send_note_comment_confirmation(*, comment):
    domain, use_https = get_domain_and_scheme()
    context = {
        "comment": comment,
        "note": comment.note,
        "student": comment.note.student_profile.user,
        "advisor": comment.author,
        "domain": domain,
        "protocol": "https" if use_https else "http",
    }
    recipients = [Recipient(email=comment.author.email, name=comment.author.get_full_name())]
    _send_email(
        subject="Your comment was sent",
        template="note_comment_confirmation",
        context=context,
        to=recipients,
    )
