import datetime

import pytest

from availability.models import Availability
from booking.models import Booking
from notes.models import NoteComment, StudentNote
from users.models import User


@pytest.fixture
@pytest.mark.django_db
def admin_user():
    return User.objects.create_user(
        email="admin@example.com",
        password="pass",
        role=User.Roles.ADMIN,
        is_staff=True,
    )


@pytest.fixture
@pytest.mark.django_db
def teacher_user():
    return User.objects.create_user(
        email="teacher@example.com",
        password="pass",
        role=User.Roles.TEACHER,
    )


@pytest.fixture
@pytest.mark.django_db
def student_user():
    return User.objects.create_user(
        email="student@example.com",
        password="pass",
        role=User.Roles.STUDENT,
    )


@pytest.fixture
@pytest.mark.django_db
def availability(teacher_user):
    return Availability.objects.create(
        teacher=teacher_user,
        date=datetime.date.today() + datetime.timedelta(days=1),
        start_time=datetime.time(9, 0),
        end_time=datetime.time(9, 30),
        meeting_type=Availability.MeetingType.ONLINE,
        message="Bring notebook",
    )


@pytest.mark.django_db
def test_booking_creation_sends_notifications(
    admin_user, teacher_user, student_user, availability, mailoutbox
):
    Booking.objects.create(availability=availability, student=student_user, message="Need help")
    assert len(mailoutbox) == 3  # student, advisor, admin
    subjects = {message.subject for message in mailoutbox}
    assert "Booking confirmed" in subjects


@pytest.mark.django_db
def test_booking_cancellation_sends_notifications(
    admin_user, student_user, availability, mailoutbox
):
    booking = Booking.objects.create(availability=availability, student=student_user)
    reason = "Need to reschedule"
    booking.cancellation_message = reason
    mailoutbox.clear()
    booking.delete()
    assert len(mailoutbox) == 3
    assert any(message.subject == "Booking cancelled" for message in mailoutbox)
    assert all(reason in message.body for message in mailoutbox)


@pytest.mark.django_db
def test_note_creation_notifies_student_and_author(teacher_user, student_user, mailoutbox):
    StudentNote.objects.create(
        student_profile=student_user.student_profile,
        title="Plan",
        body="We will review goals",
        created_by=teacher_user,
        updated_by=teacher_user,
    )
    assert len(mailoutbox) == 2
    subjects = sorted(message.subject for message in mailoutbox)
    assert subjects == ["New advisor note", "Your note was sent"]


@pytest.mark.django_db
def test_note_comment_notifications(teacher_user, student_user, mailoutbox):
    note = StudentNote.objects.create(
        student_profile=student_user.student_profile,
        title="Plan",
        body="We will review goals",
        created_by=teacher_user,
        updated_by=teacher_user,
    )
    mailoutbox.clear()
    NoteComment.objects.create(note=note, author=teacher_user, body="Looking forward")
    assert len(mailoutbox) == 2
    subjects = sorted(message.subject for message in mailoutbox)
    assert subjects == ["New comment on your note", "Your comment was sent"]
