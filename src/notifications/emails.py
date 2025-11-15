"""Notification email helpers."""

from __future__ import annotations

from dataclasses import dataclass
import html

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse

from notifications.ics import build_booking_ics
from users.utils import get_domain_and_scheme


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


@dataclass
class Recipient:
    email: str
    name: str | None = None

    def display_name(self) -> str:
        if self.name:
            return self.name
        return self.email


def _send_email(
    *,
    subject: str,
    template: str,
    context: dict,
    recipient: Recipient,
    attachments: list[tuple[str, str, str]] | None = None,
):
    """Render a notification template (txt + optional html) and send to a single recipient."""
    if not recipient or not recipient.email:
        return

    context = {"SITE_NAME": getattr(settings, "SITE_NAME", "Advising"), **context}
    context = {**context, "recipient": recipient}
    txt_body = render_to_string(f"notifications/email/{template}.txt", context)
    txt_body = html.unescape(txt_body)
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
    if attachments:
        for filename, content, mimetype in attachments:
            msg.attach(filename, content, mimetype)
    msg.send()


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
    protocol = "https" if use_https else "http"
    ics_content = build_booking_ics(booking=booking)
    attachment = (f"booking-{booking.id}.ics", ics_content, "text/calendar")

    student_recipient = Recipient(email=booking.student.email, name=booking.student.get_full_name())
    _send_email(
        subject="Booking confirmed",
        template="booking_confirmation_student",
        context={
            **context,
            "dashboard_url": f"{protocol}://{domain}{reverse('booking:book_meeting')}",
        },
        recipient=student_recipient,
        attachments=[attachment],
    )

    advisor = booking.availability.teacher
    advisor_recipient = Recipient(email=advisor.email, name=advisor.get_full_name())
    _send_email(
        subject="Booking confirmed",
        template="booking_confirmation_advisor",
        context={
            **context,
            "dashboard_url": f"{protocol}://{domain}{reverse('users:teacher_bookings')}",
        },
        recipient=advisor_recipient,
        attachments=[attachment],
    )

    admin_url = f"{protocol}://{domain}{reverse('availability:upcoming_availability')}"
    for admin in admin_recipients():
        _send_email(
            subject="Booking confirmed",
            template="booking_confirmation_admin",
            context={**context, "dashboard_url": admin_url},
            recipient=admin,
            attachments=[attachment],
        )


def send_booking_cancellation(*, booking, cancellation_message: str | None = None):
    domain, use_https = get_domain_and_scheme()
    cancellation_reason = cancellation_message or getattr(booking, "cancellation_message", "")
    context = {
        "booking": booking,
        "student": booking.student,
        "advisor": booking.availability.teacher,
        "slot": booking.availability,
        "domain": domain,
        "protocol": "https" if use_https else "http",
        "cancellation_reason": cancellation_reason,
    }
    protocol = "https" if use_https else "http"

    student_recipient = Recipient(email=booking.student.email, name=booking.student.get_full_name())
    _send_email(
        subject="Booking cancelled",
        template="booking_cancellation_student",
        context={
            **context,
            "dashboard_url": f"{protocol}://{domain}{reverse('booking:book_meeting')}",
        },
        recipient=student_recipient,
    )

    advisor = booking.availability.teacher
    advisor_recipient = Recipient(email=advisor.email, name=advisor.get_full_name())
    _send_email(
        subject="Booking cancelled",
        template="booking_cancellation_advisor",
        context={
            **context,
            "dashboard_url": f"{protocol}://{domain}{reverse('users:teacher_bookings')}",
        },
        recipient=advisor_recipient,
    )

    admin_url = f"{protocol}://{domain}{reverse('availability:upcoming_availability')}"
    for admin in admin_recipients():
        _send_email(
            subject="Booking cancelled",
            template="booking_cancellation_admin",
            context={**context, "dashboard_url": admin_url},
            recipient=admin,
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
    student_recipient = Recipient(
        email=note.student_profile.user.email,
        name=note.student_profile.user.get_full_name(),
    )
    _send_email(
        subject="New advisor note",
        template="student_note",
        context=context,
        recipient=student_recipient,
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
    advisor_recipient = Recipient(
        email=note.created_by.email,
        name=note.created_by.get_full_name(),
    )
    _send_email(
        subject="Your note was sent",
        template="note_confirmation",
        context=context,
        recipient=advisor_recipient,
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
    student_recipient = Recipient(
        email=comment.note.student_profile.user.email,
        name=comment.note.student_profile.user.get_full_name(),
    )
    _send_email(
        subject="New comment on your note",
        template="note_comment",
        context=context,
        recipient=student_recipient,
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
    author_recipient = Recipient(
        email=comment.author.email,
        name=comment.author.get_full_name(),
    )
    _send_email(
        subject="Your comment was sent",
        template="note_comment_confirmation",
        context=context,
        recipient=author_recipient,
    )
