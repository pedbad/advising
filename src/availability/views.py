"""
Views for the availability app.
"""

from datetime import date, datetime, timedelta

from django.conf import settings
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from users.decorators import role_required

from .models import Availability
from .utils import generate_time_slots, get_calendar_data, validate_date


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

    # Get calendar data with teacher availability info
    teacher = request.user if request.user.role == "teacher" else None
    calendar_data = get_calendar_data(year, month, teacher=teacher)

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

    # Generate time slots for teachers
    time_slots = []
    is_teacher = request.user.role == "teacher"
    if is_teacher:
        time_slots = generate_time_slots(selected_date, teacher=request.user)

    context = {
        "selected_date": selected_date,
        "year": year,
        "month": month,
        "day": day,
        "time_slots": time_slots,
        "is_teacher": is_teacher,
    }

    # If this is an HTMX request, return just the time slots partial
    if request.headers.get("HX-Request"):
        return render(request, "availability/partials/time_slots.html", context)

    return render(request, "availability/date_detail.html", context)


@role_required(["teacher"])
def availability_list(request):
    """
    Display a list of upcoming dates with availability slots for the teacher.

    Shows only dates that have at least one slot set, ordered chronologically.
    Only shows the actual slots that are set (not all possible time slots).
    Allows inline editing of slots.
    """
    from collections import OrderedDict

    # Show only upcoming dates (today and future)
    today = date.today()
    availabilities = Availability.objects.filter(teacher=request.user, date__gte=today).order_by(
        "date", "start_time"
    )

    # Group by date
    dates_with_slots = OrderedDict()
    for avail in availabilities:
        if avail.date not in dates_with_slots:
            dates_with_slots[avail.date] = []
        dates_with_slots[avail.date].append(avail)

    # For each date, only include the slots that are actually set
    availability_by_date = []
    for date_obj, slots in dates_with_slots.items():
        # Generate all time slots to get blocking info
        all_time_slots = generate_time_slots(date_obj, teacher=request.user)

        # Filter to only show slots that are set (is_available = True)
        set_slots = [slot for slot in all_time_slots if slot["is_available"]]

        availability_by_date.append(
            {
                "date": date_obj,
                "time_slots": set_slots,
                "slot_count": len(set_slots),
            }
        )

    context = {
        "availability_by_date": availability_by_date,
        "has_slots": len(availability_by_date) > 0,
    }

    return render(request, "availability/availability_list.html", context)


@require_http_methods(["POST"])
@role_required(["teacher"])
def save_availability(request):
    """
    AJAX endpoint to save/update/delete teacher availability.

    Expects POST data:
    - date: YYYY-MM-DD
    - start_time: HH:MM
    - meeting_type: online|in_person|both
    - action: set|delete
    """
    try:
        # Parse request data
        date_str = request.POST.get("date")
        start_time_str = request.POST.get("start_time")
        meeting_type = request.POST.get("meeting_type")
        action = request.POST.get("action", "set")

        if not all([date_str, start_time_str]):
            return JsonResponse({"success": False, "error": "Missing required fields"}, status=400)

        # Parse date and time
        selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        start_time = datetime.strptime(start_time_str, "%H:%M:%S").time()

        # Calculate end time (30 minutes later)
        meeting_duration = settings.AVAILABILITY_SETTINGS.get("MEETING_DURATION", 30)
        start_dt = datetime.combine(selected_date, start_time)
        end_time = (start_dt + timedelta(minutes=meeting_duration)).time()

        if action == "delete":
            # Delete existing availability
            Availability.objects.filter(
                teacher=request.user, date=selected_date, start_time=start_time
            ).delete()

            return JsonResponse({"success": True, "action": "deleted"})

        elif action == "set":
            # Validate meeting type
            if meeting_type not in ["online", "in_person", "both"]:
                return JsonResponse({"success": False, "error": "Invalid meeting type"}, status=400)

            # Create or update availability
            availability, created = Availability.objects.update_or_create(
                teacher=request.user,
                date=selected_date,
                start_time=start_time,
                defaults={
                    "end_time": end_time,
                    "meeting_type": meeting_type,
                },
            )

            return JsonResponse(
                {
                    "success": True,
                    "action": "created" if created else "updated",
                    "availability_id": availability.id,
                    "meeting_type": availability.meeting_type,
                }
            )

        else:
            return JsonResponse({"success": False, "error": "Invalid action"}, status=400)

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)
