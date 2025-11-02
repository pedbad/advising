"""
Calendar generation utilities for the availability app.
"""

import calendar
from datetime import date


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
