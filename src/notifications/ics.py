from __future__ import annotations

from datetime import datetime

from django.utils import timezone


def build_booking_ics(*, booking) -> str:
    slot = booking.availability
    start = timezone.make_aware(datetime.combine(slot.date, slot.start_time))
    end = timezone.make_aware(datetime.combine(slot.date, slot.end_time))

    summary = f"Session with {slot.teacher.get_full_name() or slot.teacher.email}"
    description_lines = [
        f"Student: {booking.student.get_full_name() or booking.student.email}",
        f"Advisor: {slot.teacher.get_full_name() or slot.teacher.email}",
    ]
    if slot.message:
        description_lines.append(f"Advisor note: {slot.message}")
    if booking.message:
        description_lines.append(f"Student note: {booking.message}")

    description = "\\n".join(description_lines)

    ics = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Advising//EN
BEGIN:VEVENT
UID:{uid}
DTSTAMP:{dtstamp}
DTSTART:{dtstart}
DTEND:{dtend}
SUMMARY:{summary}
DESCRIPTION:{description}
END:VEVENT
END:VCALENDAR
"""
    return ics.format(
        uid=f"booking-{booking.id}@advising",
        dtstamp=timezone.now().strftime("%Y%m%dT%H%M%SZ"),
        dtstart=start.strftime("%Y%m%dT%H%M%SZ"),
        dtend=end.strftime("%Y%m%dT%H%M%SZ"),
        summary=summary,
        description=description,
    )
