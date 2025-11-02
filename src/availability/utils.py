"""
Calendar generation utilities for the availability app.
"""

import calendar
from datetime import date, datetime, time, timedelta

from django.conf import settings


def get_calendar_data(year: int, month: int) -> dict:
    """
    Generate calendar data for a given year and month.

    Args:
        year: The year (e.g., 2025)
        month: The month (1-12)

    Returns:
        Dictionary containing:
        - year: int
        - month: int
        - month_name: str
        - weeks: List of weeks, each week is a list of dicts with day info
        - prev_month: tuple (year, month)
        - next_month: tuple (year, month)
    """
    # Get the calendar for the month
    cal = calendar.monthcalendar(year, month)
    month_name = calendar.month_name[month]

    # Get current date for highlighting
    today = date.today()

    # Build weeks with day information
    weeks = []
    for week in cal:
        week_data = []
        for day in week:
            if day == 0:
                # Empty day (from previous/next month)
                week_data.append(
                    {
                        "day": None,
                        "is_today": False,
                        "is_current_month": False,
                    }
                )
            else:
                is_today = day == today.day and month == today.month and year == today.year
                week_data.append(
                    {
                        "day": day,
                        "is_today": is_today,
                        "is_current_month": True,
                    }
                )
        weeks.append(week_data)

    # Calculate previous and next month
    prev_month = get_prev_month(year, month)
    next_month = get_next_month(year, month)

    return {
        "year": year,
        "month": month,
        "month_name": month_name,
        "weeks": weeks,
        "prev_month": prev_month,
        "next_month": next_month,
        "weekday_names": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    }


def get_prev_month(year: int, month: int) -> tuple[int, int]:
    """Get the previous month (year, month)."""
    if month == 1:
        return (year - 1, 12)
    return (year, month - 1)


def get_next_month(year: int, month: int) -> tuple[int, int]:
    """Get the next month (year, month)."""
    if month == 12:
        return (year + 1, 1)
    return (year, month + 1)


def validate_date(year: int, month: int, day: int) -> bool:
    """
    Validate if a date is valid.

    Args:
        year: Year (e.g., 2025)
        month: Month (1-12)
        day: Day (1-31)

    Returns:
        True if valid, False otherwise
    """
    try:
        date(year, month, day)
        return True
    except ValueError:
        return False


def generate_time_slots(selected_date: date, teacher=None) -> list[dict]:
    """
    Generate all available time slots for a given date.

    Each time slot is 15 minutes, but meetings are 30 minutes long,
    so selecting one slot automatically selects the next slot as well.

    Args:
        selected_date: The date to generate slots for
        teacher: Optional teacher User object to check existing availability

    Returns:
        List of time slot dictionaries with:
        - start_time: Time object
        - end_time: Time object (start_time + 30 minutes)
        - display_time: Formatted string (e.g., "8:00 AM - 8:30 AM")
        - is_available: Boolean (if teacher has set availability)
        - meeting_type: str or None (online/in_person/both)
        - availability_id: int or None (database ID if exists)
    """
    config = settings.AVAILABILITY_SETTINGS
    start_hour, start_minute = map(int, config["START_TIME"].split(":"))
    end_hour, end_minute = map(int, config["END_TIME"].split(":"))
    slot_duration = config["SLOT_DURATION"]
    meeting_duration = config["MEETING_DURATION"]

    # Get existing availabilities for this teacher and date
    existing_availabilities = {}
    if teacher:
        from .models import Availability

        availabilities = Availability.objects.filter(teacher=teacher, date=selected_date)
        for avail in availabilities:
            # Key by start_time
            existing_availabilities[avail.start_time] = {
                "meeting_type": avail.meeting_type,
                "availability_id": avail.id,
            }

    slots = []
    current_time = datetime.combine(selected_date, time(start_hour, start_minute))
    end_time_dt = datetime.combine(selected_date, time(end_hour, end_minute))

    # Get all availabilities for checking blocked slots
    all_availabilities = []
    if teacher:
        from .models import Availability

        all_availabilities = list(Availability.objects.filter(teacher=teacher, date=selected_date))

    while current_time < end_time_dt:
        slot_start = current_time.time()
        slot_end_dt = current_time + timedelta(minutes=meeting_duration)
        slot_end = slot_end_dt.time()

        # Skip this slot if the meeting would extend past the end time
        if slot_end_dt > end_time_dt:
            break

        # Check if this slot has availability (i.e., this is the start of a meeting)
        avail_data = existing_availabilities.get(slot_start)

        # Check if this slot is blocked by an existing meeting
        # A slot is blocked if it falls within an existing 30-minute meeting
        is_blocked = False
        blocking_meeting_type = None
        for availability in all_availabilities:
            # Check if current slot start time falls within this availability's meeting time
            if availability.start_time < slot_start < availability.end_time:
                is_blocked = True
                blocking_meeting_type = availability.meeting_type
                break

        slots.append(
            {
                "start_time": slot_start,
                "end_time": slot_end,
                "display_time": (
                    f"{current_time.strftime('%I:%M %p')} - "
                    f"{(current_time + timedelta(minutes=meeting_duration)).strftime('%I:%M %p')}"
                ),
                "is_available": avail_data is not None,
                "meeting_type": avail_data["meeting_type"] if avail_data else None,
                "availability_id": avail_data["availability_id"] if avail_data else None,
                "is_blocked": is_blocked,
                "blocking_meeting_type": blocking_meeting_type,
            }
        )

        # Move to next 15-minute slot
        current_time += timedelta(minutes=slot_duration)

    return slots
