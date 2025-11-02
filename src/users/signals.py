# src/users/signals.py
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction
from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver

from .utils import get_domain_and_scheme, send_invite_email

User = get_user_model()
TEACHER_GROUP_NAME = "Teacher Admin"


# -------------------------------
# Invite email after user create
# -------------------------------
@receiver(post_save, sender=User)
def send_invite_on_create(sender, instance, created: bool, **kwargs):
    """
    When a new user is created without a usable password,
    send them a set-password invite after the transaction commits.
    """
    if not created:
        return

    # Skip superusers and anyone who already has a password.
    if instance.is_superuser or instance.has_usable_password():
        return

    def _send():
        domain, use_https = get_domain_and_scheme(None)
        send_invite_email(instance, domain=domain, use_https=use_https)

    # Run only after DB commit so uid/token are valid.
    transaction.on_commit(_send)


# -------------------------------
# Teacher Admin group bootstrap
# -------------------------------


@receiver(post_migrate)
def ensure_teacher_admin_group(sender, **kwargs):
    """
    Ensure Teacher Admin group exists for potential future use.
    Teachers no longer get Django admin access (is_staff=False).
    """
    # Create the group but don't assign any special permissions or staff status
    Group.objects.get_or_create(name=TEACHER_GROUP_NAME)


# Connect after migrations (use a stable dispatch_uid to avoid double-wiring)
post_migrate.connect(
    ensure_teacher_admin_group,
    dispatch_uid="users.ensure_teacher_admin_group",
)
