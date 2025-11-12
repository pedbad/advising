from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from profiles.models import StudentProfile
from users.decorators import role_required

from .forms import NoteCommentForm, StudentNoteForm
from .models import StudentNote

User = get_user_model()


def _notes_for_profile(profile: StudentProfile):
    return (
        StudentNote.objects.filter(student_profile=profile)
        .select_related("student_profile__user", "created_by", "updated_by")
        .prefetch_related("comments__author")
    )


def _handle_note_post(request, profile: StudentProfile):
    note_form = StudentNoteForm()
    comment_form = NoteCommentForm()
    comment_form_note_id = None

    if request.method != "POST":
        return None, note_form, comment_form, comment_form_note_id

    action = request.POST.get("action")

    if action == "create_note":
        note_form = StudentNoteForm(request.POST)
        if note_form.is_valid():
            note = note_form.save(commit=False)
            note.student_profile = profile
            note.created_by = request.user
            note.updated_by = request.user
            note.last_activity_at = note.created_at
            note.save()
            messages.success(request, "Note added successfully.")
            return redirect(request.path), note_form, comment_form, comment_form_note_id
    elif action == "add_comment":
        comment_form = NoteCommentForm(request.POST)
        note_id = request.POST.get("note_id")
        note = get_object_or_404(StudentNote, id=note_id, student_profile=profile)
        comment_form_note_id = note.id
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.note = note
            comment.author = request.user
            comment.save()
            StudentNote.objects.filter(id=note.id).update(last_activity_at=comment.created_at)
            messages.success(request, "Comment added successfully.")
            return redirect(request.path), note_form, NoteCommentForm(), None

    # If we get here we either have validation errors or unsupported action
    return None, note_form, comment_form, comment_form_note_id


@role_required(["student"])
def my_notes(request):
    profile = getattr(request.user, "student_profile", None)
    if profile is None:
        messages.error(request, "Student profile not found.")
        return redirect("users:student_home")

    response, note_form, comment_form, comment_form_note_id = _handle_note_post(request, profile)
    if response:
        return response

    notes_qs = _notes_for_profile(profile)
    notes = list(notes_qs)
    error_note_id = comment_form_note_id
    admin_role = getattr(User.Roles, "ADMIN", "admin")
    teacher_role = getattr(User.Roles, "TEACHER", "teacher")
    for note in notes:
        note.comment_has_error = error_note_id == note.id
        creator_role = getattr(note.created_by, "role", "")
        if creator_role == admin_role:
            note.role_card_class = (
                "bg-amber-100 dark:bg-amber-500/20 ring-1 ring-amber-200 dark:ring-amber-400 "
                "border border-amber-300 dark:border-amber-400 text-amber-950 dark:text-amber-50"
            )
            note.role_icon_class = "text-amber-600"
            note.role_icon_full_class = "h-4 w-4 text-amber-600"
            note.role_badge_class = "bg-amber-100 text-amber-800"
            note.role_badge_label = "Admin note"
        elif creator_role == teacher_role:
            note.role_card_class = (
                "bg-sky-50 dark:bg-sky-900/30 border border-sky-200 dark:border-sky-600 "
                "text-slate-900 dark:text-slate-100"
            )
            note.role_icon_class = "text-sky-600"
            note.role_icon_full_class = "h-4 w-4 text-sky-600"
            note.role_badge_class = "bg-sky-100 text-sky-800"
            note.role_badge_label = "Advisor note"
        else:
            note.role_card_class = (
                "bg-violet-50 dark:bg-violet-900/20 border border-violet-200 dark:border-violet-600 "
                "text-violet-950 dark:text-violet-100"
            )
            note.role_icon_class = "text-violet-500"
            note.role_icon_full_class = "h-4 w-4 text-violet-500"
            note.role_badge_class = "bg-violet-100 text-violet-800"
            note.role_badge_label = "Student note"
        note.role_is_staff = creator_role in {admin_role, teacher_role}

    context = {
        "student_profile": profile,
        "notes": notes,
        "note_form": note_form,
        "comment_form": comment_form,
        "blank_comment_form": NoteCommentForm(),
        "comment_form_note_id": comment_form_note_id,
        "is_staff_view": False,
        "note_form_has_errors": bool(note_form.errors or note_form.non_field_errors()),
    }
    return render(request, "notes/student_notes.html", context)


@role_required(["teacher", "admin"])
def student_selector(request):
    query = request.GET.get("q", "").strip()
    students = (
        User.objects.filter(role=User.Roles.STUDENT)
        .select_related("student_profile")
        .order_by("last_name", "first_name")
    )

    if query:
        students = students.filter(
            Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(email__icontains=query)
        )

    context = {
        "students": students[:50],
        "search_query": query,
    }
    return render(request, "notes/student_selector.html", context)


@role_required(["teacher", "admin"])
def student_notes(request, student_id):
    profile = get_object_or_404(
        StudentProfile.objects.select_related("user"), user_id=student_id
    )

    if profile.user.role != User.Roles.STUDENT:
        messages.error(request, "Notes are only available for student accounts.")
        return redirect("notes:student_selector")

    response, note_form, comment_form, comment_form_note_id = _handle_note_post(request, profile)
    if response:
        return response

    notes_qs = _notes_for_profile(profile)
    notes = list(notes_qs)
    error_note_id = comment_form_note_id
    admin_role = getattr(User.Roles, "ADMIN", "admin")
    teacher_role = getattr(User.Roles, "TEACHER", "teacher")
    for note in notes:
        note.comment_has_error = error_note_id == note.id
        creator_role = getattr(note.created_by, "role", "")
        if creator_role == admin_role:
            note.role_card_class = (
                "bg-amber-100 dark:bg-amber-500/20 ring-1 ring-amber-200 dark:ring-amber-400 "
                "border border-amber-300 dark:border-amber-400 text-amber-950 dark:text-amber-50"
            )
            note.role_icon_class = "text-amber-600"
            note.role_icon_full_class = "h-4 w-4 text-amber-600"
            note.role_badge_class = "bg-amber-100 text-amber-800"
            note.role_badge_label = "Admin note"
        elif creator_role == teacher_role:
            note.role_card_class = (
                "bg-sky-50 dark:bg-sky-900/30 border border-sky-200 dark:border-sky-600 "
                "text-slate-900 dark:text-slate-100"
            )
            note.role_icon_class = "text-sky-600"
            note.role_icon_full_class = "h-4 w-4 text-sky-600"
            note.role_badge_class = "bg-sky-100 text-sky-800"
            note.role_badge_label = "Advisor note"
        else:
            note.role_card_class = (
                "bg-violet-50 dark:bg-violet-900/20 border border-violet-200 dark:border-violet-600 "
                "text-violet-950 dark:text-violet-100"
            )
            note.role_icon_class = "text-violet-500"
            note.role_icon_full_class = "h-4 w-4 text-violet-500"
            note.role_badge_class = "bg-violet-100 text-violet-800"
            note.role_badge_label = "Student note"
        note.role_is_staff = creator_role in {admin_role, teacher_role}

    context = {
        "student_profile": profile,
        "notes": notes,
        "note_form": note_form,
        "comment_form": comment_form,
        "blank_comment_form": NoteCommentForm(),
        "comment_form_note_id": comment_form_note_id,
        "is_staff_view": True,
        "note_form_has_errors": bool(note_form.errors or note_form.non_field_errors()),
    }
    return render(request, "notes/student_notes.html", context)
