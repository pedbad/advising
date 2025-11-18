import datetime
from html import unescape

from django.urls import reverse
import pytest

from availability.models import Availability
from booking.models import Booking
from users.models import User


@pytest.fixture
@pytest.mark.django_db
def teacher_user():
    return User.objects.create_user(
        email="teacher2@example.com",
        password="pass",
        role=User.Roles.TEACHER,
    )


@pytest.fixture
@pytest.mark.django_db
def student_user():
    return User.objects.create_user(
        email="student2@example.com",
        password="pass",
        role=User.Roles.STUDENT,
    )


@pytest.fixture
@pytest.mark.django_db
def availability(teacher_user):
    return Availability.objects.create(
        teacher=teacher_user,
        date=datetime.date.today() + datetime.timedelta(days=2),
        start_time=datetime.time(10, 0),
        end_time=datetime.time(10, 30),
        meeting_type=Availability.MeetingType.ONLINE,
    )


@pytest.fixture
@pytest.mark.django_db
def booking(availability, student_user):
    return Booking.objects.create(availability=availability, student=student_user)


@pytest.mark.django_db
def test_cancel_booking_requires_message(client, booking, student_user):
    client.force_login(student_user)
    url = reverse("booking:cancel_booking", args=[booking.id])
    response = client.post(url, data={"message": "   "})
    assert response.status_code == 400
    assert response.json()["success"] is False
    assert Booking.objects.filter(id=booking.id).exists()


@pytest.mark.django_db
def test_cancel_booking_with_message_succeeds(client, booking, student_user, mailoutbox):
    client.force_login(student_user)
    mailoutbox.clear()
    url = reverse("booking:cancel_booking", args=[booking.id])
    reason = "Can't make it"
    response = client.post(url, data={"message": reason})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert not Booking.objects.filter(id=booking.id).exists()
    assert len(mailoutbox) >= 2
    assert all(reason in unescape(message.body) for message in mailoutbox)
