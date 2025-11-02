# src/users/forms.py
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm as DjangoUserCreationForm

# Unfold-styled admin forms
from unfold.forms import (
    UserChangeForm as UnfoldUserChangeForm,
    UserCreationForm as UnfoldUserCreationForm,
)

User = get_user_model()


# --- Public (non-admin) registration form you already had --------------------
class RegisterForm(DjangoUserCreationForm):
    # expose role for now (default student)
    role = forms.ChoiceField(choices=User.Roles.choices, initial=User.Roles.STUDENT)

    class Meta(DjangoUserCreationForm.Meta):
        model = User
        # our model uses email as USERNAME_FIELD
        fields = ("email",)


# --- Profile update form (for logged-in users) ------------------------------
class ProfileUpdateForm(forms.ModelForm):
    """Form for users to update their own profile information."""

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")
        widgets = {
            "first_name": forms.TextInput(
                attrs={
                    "class": (
                        "flex h-9 w-full rounded-md border border-input bg-transparent "
                        "px-3 py-1 text-sm shadow-xs transition-colors "
                        "placeholder:text-muted-foreground focus-visible:outline-none "
                        "focus-visible:ring-1 focus-visible:ring-ring "
                        "disabled:cursor-not-allowed disabled:opacity-50"
                    ),
                    "placeholder": "First name",
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "class": (
                        "flex h-9 w-full rounded-md border border-input bg-transparent "
                        "px-3 py-1 text-sm shadow-xs transition-colors "
                        "placeholder:text-muted-foreground focus-visible:outline-none "
                        "focus-visible:ring-1 focus-visible:ring-ring "
                        "disabled:cursor-not-allowed disabled:opacity-50"
                    ),
                    "placeholder": "Last name",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": (
                        "flex h-9 w-full rounded-md border border-input bg-transparent "
                        "px-3 py-1 text-sm shadow-xs transition-colors "
                        "placeholder:text-muted-foreground focus-visible:outline-none "
                        "focus-visible:ring-1 focus-visible:ring-ring "
                        "disabled:cursor-not-allowed disabled:opacity-50"
                    ),
                    "placeholder": "Email address",
                }
            ),
        }

    def clean_email(self):
        """Ensure email is unique, excluding the current user."""
        email = self.cleaned_data.get("email")
        if User.objects.exclude(pk=self.instance.pk).filter(email=email).exists():
            raise forms.ValidationError("This email address is already in use.")
        return email


# --- Admin-only forms (Unfold-styled) ---------------------------------------
class AdminUserAddForm(UnfoldUserCreationForm):
    """Used by Django admin Add User page (gives Unfold-styled password1/2)."""

    class Meta(UnfoldUserCreationForm.Meta):
        model = User
        fields = ("email",)  # password1/password2 come from parent form


class AdminUserChangeForm(UnfoldUserChangeForm):
    """Used by Django admin Change User page (Unfold-styled widgets)."""

    class Meta(UnfoldUserChangeForm.Meta):
        model = User
        fields = (
            "email",
            "first_name",
            "last_name",
            "role",
            "is_active",
            "is_staff",
            "is_superuser",
            "groups",
            "user_permissions",
        )
