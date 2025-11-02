"""
Views for the availability app.
"""

from datetime import date

from django.http import Http404
from django.shortcuts import redirect, render

from users.decorators import role_required

from .utils import get_calendar_data, validate_date


@role_required(["teacher", "admin"])
def calendar_view(request, year=None, month=None):
    """
    Display a monthly calendar view.

    If year/month are not provided, defaults to current month.
    """
    today = date.today()

    # Default to current year/month if not provided
    if year is None or month is None:
        year = today.year
        month = today.month

    # Validate year and month
    try:
        year = int(year)
        month = int(month)
        if not (1 <= month <= 12):
            raise ValueError("Invalid month")
    except (ValueError, TypeError):
        # Invalid year/month, redirect to current month
        return redirect("availability:calendar")

    # Get calendar data
    calendar_data = get_calendar_data(year, month)

    context = {
        "calendar": calendar_data,
    }

    return render(request, "availability/calendar.html", context)


@role_required(["teacher", "admin"])
def date_detail_view(request, year, month, day):
    """
    Display details for a specific date.

    Shows the selected date information.
    Can be extended later to show appointments, notes, etc.
    """
    # Validate the date
    try:
        year = int(year)
        month = int(month)
        day = int(day)

        if not validate_date(year, month, day):
            raise Http404("Invalid date")

        selected_date = date(year, month, day)
    except (ValueError, TypeError):
        raise Http404("Invalid date")

    context = {
        "selected_date": selected_date,
        "year": year,
        "month": month,
        "day": day,
    }

    return render(request, "availability/date_detail.html", context)
