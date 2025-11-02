"""
Management command to remove Django admin staff access from teachers.
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = "Remove is_staff flag from all teacher users (admins only should have admin access)"

    def handle(self, *args, **options):
        teachers = User.objects.filter(role=User.Roles.TEACHER, is_staff=True)
        count = teachers.count()

        if count == 0:
            self.stdout.write(
                self.style.SUCCESS("✓ No teachers with staff access found. All good!")
            )
            return

        # Update all teachers to remove staff access
        teachers.update(is_staff=False)

        self.stdout.write(
            self.style.SUCCESS(f"✓ Successfully removed staff access from {count} teacher(s)")
        )
        self.stdout.write("  Teachers can no longer access the Django admin backend.")
