# src/users/urls.py
from django.urls import path

from . import views

app_name = "users"

urlpatterns = [
    # auth
    path("login/", views.EmailLoginView.as_view(), name="login"),
    path("logout/", views.EmailLogoutView.as_view(), name="logout"),
    path("register/", views.RegisterView.as_view(), name="register"),
    # dashboards / placeholders (so redirects resolve without other apps)
    path("student/", views.student_home, name="student_home"),
    path("student/book-meeting/", views.book_meeting, name="book_meeting"),
    path("student/cancel-booking/<int:booking_id>/", views.cancel_booking, name="cancel_booking"),
    path("teacher/", views.teacher_home, name="teacher_home"),
    path("teacher/calendar/", views.teacher_calendar, name="teacher_calendar"),
    path("admin-home/", views.admin_home, name="admin_home"),
    path(
        "admin/teacher/<int:teacher_id>/calendar/",
        views.admin_teacher_calendar,
        name="admin_teacher_calendar",
    ),
    # admin lists
    path("students/", views.student_list, name="student_list"),
    path("teachers/", views.teacher_list, name="teacher_list"),
    # profile
    path("profile/", views.profile_view, name="profile"),
    path("profile/edit/", views.profile_edit, name="profile_edit"),
    path("profile/change-password/", views.change_password, name="change_password"),
    # password reset (Django's built-in views, via our wrappers)
    path("password-reset/", views.PasswordResetStartView.as_view(), name="password_reset"),
    path(
        "password-reset/done/",
        views.PasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        views.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        views.PasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
]
