from django.contrib import admin

from .models import NoteComment, StudentNote


class NoteCommentInline(admin.TabularInline):
    model = NoteComment
    extra = 0
    readonly_fields = ("author", "body", "created_at", "updated_at")


@admin.register(StudentNote)
class StudentNoteAdmin(admin.ModelAdmin):
    list_display = ("student_profile", "title", "created_by", "created_at")
    list_filter = ("created_at",)
    search_fields = (
        "student_profile__user__email",
        "student_profile__user__first_name",
        "student_profile__user__last_name",
        "title",
        "body",
    )
    autocomplete_fields = ("student_profile", "created_by", "updated_by")
    inlines = [NoteCommentInline]


@admin.register(NoteComment)
class NoteCommentAdmin(admin.ModelAdmin):
    list_display = ("note", "author", "created_at")
    search_fields = ("body", "author__email")
    autocomplete_fields = ("note", "author")
