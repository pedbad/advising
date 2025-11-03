"""
Signals for the profiles app.
"""

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import StudentProfile

User = get_user_model()


@receiver(post_save, sender=User)
def create_student_profile(sender, instance, created, **kwargs):
    """
    Automatically create a StudentProfile when a new student user is created.
    """
    if created and instance.role == "student":
        StudentProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_student_profile(sender, instance, **kwargs):
    """
    Save the StudentProfile when the user is saved.
    """
    if instance.role == "student" and hasattr(instance, "student_profile"):
        instance.student_profile.save()
