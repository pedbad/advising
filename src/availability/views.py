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
    For admins, can view a specific teacher's calendar via teacher_id param.
    """
    from django.shortcuts import get_object_or_404

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

    # Determine which teacher's calendar to show
    viewing_teacher = None
    is_admin_view = False

    if request.user.role == "admin":
        # Admin viewing a teacher's calendar
        teacher_id = request.GET.get("teacher_id")
        if teacher_id:
            from django.contrib.auth import get_user_model

            User = get_user_model()
            viewing_teacher = get_object_or_404(User, id=teacher_id, role="teacher")
            is_admin_view = True
            teacher = viewing_teacher
        else:
            teacher = None
    else:
        # Teacher viewing their own calendar
        viewing_teacher = request.user
        teacher = request.user

    # Get calendar data with teacher availability info
    calendar_data = get_calendar_data(year, month, teacher=teacher)

    context = {
        "calendar": calendar_data,
        "viewing_teacher": viewing_teacher,
        "is_admin_view": is_admin_view,
    }

    return render(request, "availability/calendar.html", context)


@role_required(["teacher", "admin"])
def date_detail_view(request, year, month, day):
    """
    Display details for a specific date.

    Shows the selected date information.
    For admins, they can view/edit availability for a teacher specified by teacher_id param.
    """
    from django.shortcuts import get_object_or_404

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

    # Determine which teacher's calendar to show
    viewing_teacher = None
    is_admin_view = False

    if request.user.role == "admin":
        # Admin viewing a teacher's calendar
        teacher_id = request.GET.get("teacher_id")
        if teacher_id:
            from django.contrib.auth import get_user_model

            User = get_user_model()
            viewing_teacher = get_object_or_404(User, id=teacher_id, role="teacher")
            is_admin_view = True
        time_slots = (
            generate_time_slots(selected_date, teacher=viewing_teacher) if viewing_teacher else []
        )
    else:
        # Teacher viewing their own calendar
        viewing_teacher = request.user
        time_slots = generate_time_slots(selected_date, teacher=request.user)

    # Calculate previous and next dates for navigation
    from datetime import date as date_class

    prev_date = selected_date - timedelta(days=1)
    next_date = selected_date + timedelta(days=1)
    today = date_class.today()
    show_prev = prev_date >= today  # Only show previous button if not going to past

    context = {
        "selected_date": selected_date,
        "year": year,
        "month": month,
        "day": day,
        "time_slots": time_slots,
        "is_teacher": viewing_teacher is not None,
        "viewing_teacher": viewing_teacher,
        "is_admin_view": is_admin_view,
        "prev_date": prev_date,
        "next_date": next_date,
        "show_prev": show_prev,
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


@role_required(["admin"])
def upcoming_availability_list(request):
    """
    Display a list of all upcoming availability slots from all teachers.

    Admin-only view that shows all availability slots from today onwards,
    with options to filter by meeting type and group by teacher or date.
    """
    from collections import OrderedDict

    # Show only upcoming dates (today and future)
    today = date.today()
    tomorrow = today + timedelta(days=1)
    availabilities = (
        Availability.objects.filter(date__gte=today)
        .select_related("teacher")
        .order_by("date", "start_time", "teacher__last_name", "teacher__first_name")
    )

    # Prepare data for both grouping options
    # Group by teacher
    by_teacher = OrderedDict()
    for avail in availabilities:
        teacher_key = avail.teacher.id
        if teacher_key not in by_teacher:
            by_teacher[teacher_key] = {
                "teacher": avail.teacher,
                "slots": [],
            }
        by_teacher[teacher_key]["slots"].append(avail)

    # Group by date
    by_date = OrderedDict()
    for avail in availabilities:
        if avail.date not in by_date:
            by_date[avail.date] = []
        by_date[avail.date].append(avail)

    context = {
        "availabilities_by_teacher": list(by_teacher.values()),
        "availabilities_by_date": by_date,
        "has_slots": len(availabilities) > 0,
        "today": today,
        "tomorrow": tomorrow,
    }

    return render(request, "availability/upcoming_availability.html", context)


@require_http_methods(["POST"])
@role_required(["teacher", "admin"])
def save_availability(request):
    """
    AJAX endpoint to save/update/delete teacher availability.

    Expects POST data:
    - date: YYYY-MM-DD
    - start_time: HH:MM
    - meeting_type: online|in_person|both
    - message: (optional) short message or note for the time slot
    - action: set|delete
    - teacher_id: (optional, for admin editing on behalf of teacher)
    """
    from django.shortcuts import get_object_or_404

    try:
        # Parse request data
        date_str = request.POST.get("date")
        start_time_str = request.POST.get("start_time")
        meeting_type = request.POST.get("meeting_type")
        message = request.POST.get("message", "")
        action = request.POST.get("action", "set")
        teacher_id = request.POST.get("teacher_id")

        if not all([date_str, start_time_str]):
            return JsonResponse({"success": False, "error": "Missing required fields"}, status=400)

        # Determine which teacher's availability to modify
        if request.user.role == "admin" and teacher_id:
            # Admin editing on behalf of a teacher
            from django.contrib.auth import get_user_model

            User = get_user_model()
            teacher = get_object_or_404(User, id=teacher_id, role="teacher")
        else:
            # Teacher editing their own availability
            teacher = request.user

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
                teacher=teacher, date=selected_date, start_time=start_time
            ).delete()

            return JsonResponse({"success": True, "action": "deleted"})

        elif action == "set":
            # Validate meeting type
            if meeting_type not in ["online", "in_person", "both"]:
                return JsonResponse({"success": False, "error": "Invalid meeting type"}, status=400)

            # Create or update availability
            availability, created = Availability.objects.update_or_create(
                teacher=teacher,
                date=selected_date,
                start_time=start_time,
                defaults={
                    "end_time": end_time,
                    "meeting_type": meeting_type,
                    "message": message,
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
