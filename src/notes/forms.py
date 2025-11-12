from django import forms

from .models import NoteComment, StudentNote


INPUT_CLS = (
    "flex w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm "
    "shadow-xs transition-colors placeholder:text-muted-foreground focus-visible:outline-none "
    "focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
)


class StudentNoteForm(forms.ModelForm):
    class Meta:
        model = StudentNote
        fields = ("title", "body")
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": INPUT_CLS,
                    "placeholder": "Optional subject line",
                }
            ),
            "body": forms.Textarea(
                attrs={
                    "class": f"{INPUT_CLS} min-h-[120px]",
                    "placeholder": "Write your note...",
                }
            ),
        }


class NoteCommentForm(forms.ModelForm):
    class Meta:
        model = NoteComment
        fields = ("body",)
        widgets = {
            "body": forms.Textarea(
                attrs={
                    "class": f"{INPUT_CLS} min-h-[80px]",
                    "placeholder": "Add a comment...",
                }
            )
        }
