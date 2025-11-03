"""
Forms for the questionnaire app.
"""

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Questionnaire


class QuestionnaireForm(forms.ModelForm):
    """
    Form for students to complete their questionnaire.
    """

    LANGUAGE_GOALS_CHOICES = [
        ("personal_interest", "Personal or general interest"),
        ("fieldwork", "Fieldwork (oral communicative purposes)"),
        ("academic_reading", "Academic reading or other scholarship"),
        ("study_abroad", "Preparation for work or study abroad"),
        ("other", "Other"),
    ]

    language_mandatory_goals = forms.MultipleChoiceField(
        choices=LANGUAGE_GOALS_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Learning / Development Goals (Mandatory Language)",
        help_text="Select all that apply",
    )

    language_optional_goals = forms.MultipleChoiceField(
        choices=LANGUAGE_GOALS_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Learning / Development Goals (Optional Language)",
        help_text="Select all that apply (if you specified a second language)",
    )

    class Meta:
        model = Questionnaire
        fields = [
            "faculty_department",
            "mother_tongue",
            "university_status",
            "language_mandatory_name",
            "language_mandatory_proficiency",
            "language_mandatory_goals",
            "language_optional_name",
            "language_optional_proficiency",
            "language_optional_goals",
            "aspects_to_improve",
            "activities_you_can_manage",
            "hours_per_week",
            "other_languages_studied",
            "additional_comments",
        ]
        widgets = {
            "university_status": forms.RadioSelect(),
            "language_mandatory_proficiency": forms.RadioSelect(),
            "language_optional_proficiency": forms.RadioSelect(),
            "faculty_department": forms.TextInput(
                attrs={
                    "placeholder": 'e.g., Computer Science, or type "External" if not applicable'
                }
            ),
            "mother_tongue": forms.TextInput(attrs={"placeholder": "e.g., English, Spanish, etc."}),
            "language_mandatory_name": forms.TextInput(
                attrs={"placeholder": "e.g., French, German, etc."}
            ),
            "language_optional_name": forms.TextInput(
                attrs={"placeholder": "e.g., Italian, Japanese, etc. (optional)"}
            ),
            "aspects_to_improve": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": (
                        "What specific skills would you like to develop? "
                        "(e.g., speaking, writing, grammar, etc.)"
                    ),
                }
            ),
            "activities_you_can_manage": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Describe what you can currently do in the language(s)",
                }
            ),
            "hours_per_week": forms.TextInput(attrs={"placeholder": "e.g., 5-10 hours"}),
            "other_languages_studied": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "List any languages you have studied before (optional)",
                }
            ),
            "additional_comments": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Any other information you would like to share (optional)",
                }
            ),
        }
        labels = {
            "faculty_department": "Faculty / Department",
            "mother_tongue": "Mother Tongue / First Language",
            "university_status": "University Status",
            "language_mandatory_name": "Main Language to Learn or Improve",
            "language_mandatory_proficiency": "Current Proficiency (Mandatory Language)",
            "language_optional_name": "Additional Language (Optional)",
            "language_optional_proficiency": "Current Proficiency (Optional Language)",
            "aspects_to_improve": "What aspects would you like to learn or improve?",
            "activities_you_can_manage": "What activities can you currently manage?",
            "hours_per_week": "Hours per week for language learning",
            "other_languages_studied": "Other languages previously studied",
            "additional_comments": "Additional comments",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Remove the blank choice for required fields
        self.fields["university_status"].choices = [
            c for c in self.fields["university_status"].choices if c[0] != ""
        ]
        self.fields["language_mandatory_proficiency"].choices = [
            c for c in self.fields["language_mandatory_proficiency"].choices if c[0] != ""
        ]
        self.fields["language_optional_proficiency"].choices = [
            c for c in self.fields["language_optional_proficiency"].choices if c[0] != ""
        ]

    def clean_language_mandatory_goals(self):
        """Ensure at least one learning goal is selected for mandatory language."""
        data = self.cleaned_data.get("language_mandatory_goals")
        if not data:
            raise forms.ValidationError(_("Please select at least one learning goal."))
        return data

    def clean_other_languages_studied(self):
        """Set default value if not specified."""
        data = self.cleaned_data.get("other_languages_studied")
        if not data or not data.strip():
            return "Not specified"
        return data

    def clean(self):
        """Additional validation for optional language fields."""
        cleaned_data = super().clean()

        optional_name = cleaned_data.get("language_optional_name")
        optional_proficiency = cleaned_data.get("language_optional_proficiency")
        optional_goals = cleaned_data.get("language_optional_goals")

        # If optional language name is provided, require proficiency and goals
        if optional_name and optional_name.strip():
            if not optional_proficiency:
                self.add_error(
                    "language_optional_proficiency",
                    "Please select a proficiency level for the optional language.",
                )
            if not optional_goals:
                self.add_error(
                    "language_optional_goals",
                    "Please select at least one learning goal for the optional language.",
                )

        return cleaned_data
