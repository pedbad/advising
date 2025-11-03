"""
Views for the questionnaire app.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from .forms import QuestionnaireForm


@login_required
def questionnaire_view(request, student_id=None):
    """
    Students: view/edit own questionnaire
    Teachers/Admins: view a student's questionnaire (read-only)
    """
    # Determine whose questionnaire is being viewed
    if student_id is not None:
        # Only staff (teacher/admin) can view another student's page
        if request.user.role not in ("teacher", "admin"):
            return HttpResponseForbidden("Not allowed")

        from django.contrib.auth import get_user_model

        User = get_user_model()
        student = get_object_or_404(User, id=student_id, role="student")
        student_profile = getattr(student, "student_profile", None)

        if not student_profile:
            return render(request, "404.html", status=404)

        is_owner = False
        is_editing = False  # staff cannot edit
    else:
        # Student viewing their own
        student = request.user

        # Ensure student has a profile
        if not hasattr(student, "student_profile"):
            messages.error(request, "Student profile not found. Please contact support.")
            return redirect("users:student_home")

        student_profile = student.student_profile
        is_owner = True
        is_editing = request.GET.get("edit", "false").lower() == "true"

    # Check if student has completed questionnaire
    has_completed = student_profile.has_completed_questionnaire()

    # Force edit if owner has never completed
    if is_owner and not has_completed:
        is_editing = True

    # Get latest questionnaire
    latest_questionnaire = student_profile.questionnaires.order_by("-created_at").first()

    if request.method == "POST" and is_owner and is_editing:
        form = QuestionnaireForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.student_profile = student_profile
            obj.completed = True
            obj.save()
            messages.success(request, "Your questionnaire has been submitted successfully!")
            # Redirect to student home
            return redirect("users:student_home")
    else:
        form = QuestionnaireForm(instance=latest_questionnaire)

    return render(
        request,
        "questionnaire/questionnaire.html",
        {
            "form": form,
            "is_editing": is_editing,
            "student": student,
            "latest_questionnaire": latest_questionnaire,
            "questionnaires": student_profile.questionnaires.filter(completed=True).order_by(
                "-created_at"
            ),
            "has_completed_questionnaire": has_completed,
            "is_owner": is_owner,
        },
    )
