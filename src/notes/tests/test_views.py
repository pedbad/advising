from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import NoteComment, StudentNote


class NotesViewsTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.student = self.User.objects.create_user(
            email="student@example.com",
            password="pass1234",
            role=self.User.Roles.STUDENT,
        )
        self.teacher = self.User.objects.create_user(
            email="teacher@example.com",
            password="pass1234",
            role=self.User.Roles.TEACHER,
        )

    def test_student_can_create_note(self):
        self.client.login(email=self.student.email, password="pass1234")
        url = reverse("notes:my_notes")
        response = self.client.post(
            url,
            {
                "action": "create_note",
                "title": "First",
                "body": "Hello from student",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        note = StudentNote.objects.get()
        self.assertEqual(note.student_profile, self.student.student_profile)
        self.assertEqual(note.created_by, self.student)

    def test_teacher_can_comment_on_student_note(self):
        note = StudentNote.objects.create(
            student_profile=self.student.student_profile,
            title="Plan",
            body="Initial note",
            created_by=self.student,
        )
        self.client.login(email=self.teacher.email, password="pass1234")
        url = reverse("notes:student_notes", args=[self.student.id])
        response = self.client.post(
            url,
            {
                "action": "add_comment",
                "note_id": note.id,
                "body": "Teacher feedback",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        comment = NoteComment.objects.get()
        self.assertEqual(comment.author, self.teacher)
        self.assertEqual(comment.note, note)

    def test_student_selector_requires_staff(self):
        self.client.login(email=self.student.email, password="pass1234")
        url = reverse("notes:student_selector")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
