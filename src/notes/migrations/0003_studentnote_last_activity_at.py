from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("notes", "0002_rename_notes_note_student_6dd17b_idx_notes_stude_student_43b846_idx"),
    ]

    operations = [
        migrations.AddField(
            model_name="studentnote",
            name="last_activity_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterModelOptions(
            name="studentnote",
            options={"ordering": ["-last_activity_at", "-created_at"]},
        ),
    ]
