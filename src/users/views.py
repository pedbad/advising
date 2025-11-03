# users/views.py

# Django imports
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView

# Local imports
from .constants import PWD_RESET_TPLS  # ← centralised template names
from .decorators import role_required
from .forms import ProfileUpdateForm, RegisterForm
from .mixins import AdminRequiredMixin

User = get_user_model()


def _redirect_for_role(user: AbstractBaseUser) -> str:
    """
    Map user.role → URL name, with sane fallbacks and support for @override_settings.
    Priority:
      1) settings.USERS_ROLE_REDIRECTS (if provided in runtime/tests)
      2) sensible defaults for known roles (admin/teacher/student)
    """
    role = getattr(user, "role", None)

    # 1) Honor dynamic settings (override_settings in tests will work here)
    mapping = getattr(settings, "USERS_ROLE_REDIRECTS", {}) or {}
    url_name = mapping.get(role)
    if url_name:
        return reverse(url_name)

    # 2) Sane defaults if the mapping is missing/incomplete
    try:
        # Use your project enum if present
        teacher_val = getattr(User.Roles, "TEACHER", "teacher")
        admin_val = getattr(User.Roles, "ADMIN", "admin")
    except Exception:
        teacher_val, admin_val = "teacher", "admin"

    if role == admin_val:
        return reverse("users:admin_home")
    if role == teacher_val:
        return reverse("users:teacher_home")

    # default (student or unknown)
    return reverse("users:student_home")


# --------------------------
# Auth: login / logout
# --------------------------
class EmailLoginView(LoginView):
    template_name = "users/registration/login.html"

    def get_success_url(self):
        user = self.request.user

        # Check if user is a student and has not completed questionnaire
        if user.role == "student":
            # Check if student profile exists and questionnaire is incomplete
            if hasattr(user, "student_profile"):
                if not user.student_profile.has_completed_questionnaire():
                    return reverse("questionnaire:questionnaire")

        return _redirect_for_role(user)


class EmailLogoutView(LogoutView):
    # render a page instead of redirecting
    next_page = None
    template_name = "users/registration/logged_out.html"


# --------------------------
# Auth: register
# --------------------------
class RegisterView(AdminRequiredMixin, CreateView):
    template_name = "users/registration/register.html"
    model = User
    form_class = RegisterForm
    success_url = reverse_lazy("users:student_home")  # fallback

    @transaction.atomic
    def form_valid(self, form):
        user = form.save(commit=False)
        user.role = form.cleaned_data.get("role", User.Roles.STUDENT)

        # require first-time set password
        user.set_unusable_password()

        # Only admins get staff access to Django admin
        if user.role == User.Roles.ADMIN:
            user.is_staff = True

        # ✅ save BEFORE touching many-to-many relations
        user.save()

        messages.success(
            self.request,
            f"User {user.email} created. An invite email will be sent automatically.",
        )

        # Redirect the creator (admin/teacher), not the new user
        return redirect(_redirect_for_role(self.request.user))


# --------------------------
# Password reset flow (centralised via PWD_RESET_TPLS)
# --------------------------
class PasswordResetStartView(PasswordResetView):
    template_name = PWD_RESET_TPLS["form"]
    email_template_name = PWD_RESET_TPLS["email_txt"]
    subject_template_name = PWD_RESET_TPLS["subject"]
    html_email_template_name = PWD_RESET_TPLS.get("email_html")
    success_url = reverse_lazy("users:password_reset_done")


class PasswordResetDoneView(PasswordResetDoneView):
    template_name = PWD_RESET_TPLS["done"]


class PasswordResetConfirmView(PasswordResetConfirmView):
    template_name = PWD_RESET_TPLS["confirm"]
    success_url = reverse_lazy("users:password_reset_complete")


class PasswordResetCompleteView(PasswordResetCompleteView):
    template_name = PWD_RESET_TPLS["complete"]


# --------------------------
# Simple role home placeholders
# --------------------------


@role_required(["student"])
def student_home(request):
    return render(request, "users/student_home.html")


@role_required(["teacher"])
def teacher_home(request):
    """Teacher home page placeholder."""
    return render(request, "users/teacher_home.html")


@role_required(["teacher"])
def teacher_calendar(request):
    """Teacher calendar view."""
    from datetime import date

    from availability.utils import get_calendar_data

    today = date.today()
    calendar_data = get_calendar_data(today.year, today.month, teacher=request.user)

    context = {
        "calendar": calendar_data,
    }

    return render(request, "users/teacher_calendar.html", context)


@role_required(["admin"])
def admin_home(request):
    """Admin home page placeholder."""
    return render(request, "users/admin_home.html")


@role_required(["admin"])
def admin_teacher_calendar(request, teacher_id):
    """
    Admin view of a specific teacher's calendar.

    Allows admins to view and manage availability on behalf of a teacher.
    """
    from datetime import date

    from django.shortcuts import get_object_or_404

    from availability.utils import get_calendar_data

    # Get the teacher
    teacher = get_object_or_404(User, id=teacher_id, role=User.Roles.TEACHER)

    today = date.today()
    calendar_data = get_calendar_data(today.year, today.month, teacher=teacher)

    context = {
        "calendar": calendar_data,
        "viewing_teacher": teacher,  # Pass the teacher being viewed
        "is_admin_view": True,  # Flag to indicate admin is viewing
    }

    return render(request, "users/admin_teacher_calendar.html", context)


# --------------------------
# Profile views
# --------------------------


@login_required
def profile_view(request):
    """View user profile information."""
    return render(request, "users/profile.html", {"user": request.user})


@login_required
def profile_edit(request):
    """Edit user profile information."""
    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully.")
            return redirect("users:profile")
    else:
        form = ProfileUpdateForm(instance=request.user)

    return render(request, "users/profile_edit.html", {"form": form})


@login_required
def change_password(request):
    """Change user password."""
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Keep the user logged in after password change
            update_session_auth_hash(request, user)
            messages.success(request, "Your password has been changed successfully.")
            return redirect("users:profile")
    else:
        form = PasswordChangeForm(request.user)

    return render(request, "users/change_password.html", {"form": form})


# --------------------------
# Admin user lists
# --------------------------


@role_required(["teacher", "admin"])
def student_list(request):
    """List all students for teachers and admins."""
    students = User.objects.filter(role=User.Roles.STUDENT).order_by(
        "last_name", "first_name", "email"
    )
    return render(request, "users/student_list.html", {"students": students})


@role_required(["admin"])
def teacher_list(request):
    """List all teachers for admin."""
    teachers = User.objects.filter(role=User.Roles.TEACHER).order_by(
        "last_name", "first_name", "email"
    )
    return render(request, "users/teacher_list.html", {"teachers": teachers})
