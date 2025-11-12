"""
Views for the booking app.
"""

from collections import OrderedDict
from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, render

from availability.models import Availability
from booking.models import Booking
from notifications.ics import build_booking_ics
from users.decorators import role_required


@role_required(["student"])
def book_meeting(request):
    """
    Book a meeting page for students.

    Shows available slots and allows booking.
    Requires questionnaire completion to view/book slots.
    """
    # Check if student has completed questionnaire
    has_completed = request.user.student_profile.has_completed_questionnaire()

    if not has_completed:
        return render(
            request,
            "booking/book_meeting.html",
            {"has_completed_questionnaire": False},
        )

    # Handle booking POST request
    if request.method == "POST":
        availability_id = request.POST.get("availability_id")
        message = request.POST.get("message", "").strip()

        if availability_id:
            try:
                with transaction.atomic():
                    # Lock the availability row to prevent race conditions
                    availability = (
                        Availability.objects.select_for_update()
                        .select_related("teacher")
                        .get(id=availability_id)
                    )

                    # Check if already booked
                    if hasattr(availability, "booking"):
                        return JsonResponse(
                            {"success": False, "error": "This slot has already been booked."},
                            status=400,
                        )

                    # Check if student already has a booking on this date
                    existing_booking_on_date = Booking.objects.filter(
                        student=request.user, availability__date=availability.date
                    ).exists()

                    if existing_booking_on_date:
                        return JsonResponse(
                            {
                                "success": False,
                                "error": (
                                    "You already have a booking on this date. "
                                    "You can only book one slot per day."
                                ),
                            },
                            status=400,
                        )

                    # Create the booking
                    booking = Booking.objects.create(
                        availability=availability, student=request.user, message=message
                    )

                    confirmation_msg = (
                        "Booking confirmed! Your "
                        f"{availability.get_meeting_type_display()} appointment with "
                        f"{availability.teacher.get_full_name() or availability.teacher.email} "
                        f"on {availability.date.strftime('%B %d, %Y')} "
                        f"at {availability.start_time.strftime('%-I:%M %p')} "
                        "has been scheduled."
                    )

                    messages.success(request, confirmation_msg)

                    return JsonResponse(
                        {
                            "success": True,
                            "message": "Booking confirmed successfully!",
                            "booking_id": booking.id,
                        }
                    )

            except Availability.DoesNotExist:
                return JsonResponse(
                    {"success": False, "error": "Availability slot not found."}, status=404
                )
            except Exception as e:
                return JsonResponse({"success": False, "error": str(e)}, status=500)

    # GET request - show available slots
    today = date.today()
    tomorrow = today + timedelta(days=1)

    # Fetch all upcoming availability slots (both booked and unbooked)
    availabilities = (
        Availability.objects.filter(date__gte=today)
        .select_related("teacher")
        .prefetch_related("booking")
        .order_by("date", "start_time", "teacher__last_name", "teacher__first_name")
    )

    # Get student's own bookings
    student_booking_ids = set(
        Booking.objects.filter(student=request.user, availability__date__gte=today).values_list(
            "availability_id", flat=True
        )
    )

    # Create a mapping of availability_id to booking for student's bookings
    student_bookings_dict = {
        booking.availability_id: booking
        for booking in Booking.objects.filter(
            student=request.user, availability__date__gte=today
        ).select_related("availability")
    }

    # Filter slots: show unbooked OR booked by current student (hide booked by others)
    filtered_availabilities = []
    for avail in availabilities:
        is_booked_by_others = hasattr(avail, "booking") and avail.booking.student != request.user
        if not is_booked_by_others:
            # Add flag to indicate if this is the student's booking
            avail.is_my_booking = avail.id in student_booking_ids
            # Attach booking object if it's the student's booking
            if avail.is_my_booking:
                avail.booking = student_bookings_dict.get(avail.id)
            filtered_availabilities.append(avail)

    # Group by teacher
    by_teacher = OrderedDict()
    for avail in filtered_availabilities:
        teacher_key = avail.teacher.id
        if teacher_key not in by_teacher:
            by_teacher[teacher_key] = {
                "teacher": avail.teacher,
                "slots": [],
            }
        by_teacher[teacher_key]["slots"].append(avail)

    # Group by date
    by_date = OrderedDict()
    for avail in filtered_availabilities:
        if avail.date not in by_date:
            by_date[avail.date] = []
        by_date[avail.date].append(avail)

    # Get dates where student has bookings (for disabling other slots on same date)
    booked_dates = list(
        Booking.objects.filter(student=request.user, availability__date__gte=today)
        .values_list("availability__date", flat=True)
        .distinct()
    )
    booked_dates_iso = [d.isoformat() for d in booked_dates]

    context = {
        "has_completed_questionnaire": True,
        "availabilities_by_teacher": list(by_teacher.values()),
        "availabilities_by_date": by_date,
        "has_slots": len(filtered_availabilities) > 0,
        "today": today,
        "tomorrow": tomorrow,
        "booked_dates": booked_dates_iso,
    }

    return render(request, "booking/book_meeting.html", context)


@role_required(["student"])
def cancel_booking(request, booking_id):
    """
    Cancel a booking for a student.

    Only allows students to cancel their own bookings.
    """
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid request method."}, status=405)

    try:
        # Get the booking and ensure it belongs to the current student
        booking = get_object_or_404(
            Booking.objects.select_related("availability", "availability__teacher"),
            id=booking_id,
            student=request.user,
        )

        # Store booking info for success message
        availability = booking.availability
        teacher_name = availability.teacher.get_full_name() or availability.teacher.email
        date_str = availability.date.strftime("%B %d, %Y")
        time_str = availability.start_time.strftime("%-I:%M %p")
        meeting_type = availability.get_meeting_type_display()

        # Delete the booking
        booking.delete()

        cancel_msg = (
            "Booking cancelled. "
            f"Your {meeting_type} appointment with {teacher_name} on {date_str} "
            f"at {time_str} has been cancelled."
        )

        messages.success(request, cancel_msg)

        return JsonResponse({"success": True, "message": "Booking cancelled successfully."})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@login_required
def booking_ics(request, booking_id):
    booking = get_object_or_404(
        Booking.objects.select_related("availability", "availability__teacher", "student"),
        id=booking_id,
    )
    user = request.user
    role = getattr(user, "role", "")
    if not (
        role == "admin"
        or booking.student_id == user.id
        or booking.availability.teacher_id == user.id
    ):
        return HttpResponseForbidden("You do not have permission to download this event.")

    ics_content = build_booking_ics(booking=booking)
    response = HttpResponse(ics_content, content_type="text/calendar")
    response["Content-Disposition"] = f'attachment; filename="booking-{booking.id}.ics"'
    return response
