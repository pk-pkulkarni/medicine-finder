from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Patient",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=160)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Document",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("file", models.FileField(upload_to="prescriptions/%Y/%m/")),
                ("original_name", models.CharField(max_length=260)),
                ("file_type", models.CharField(blank=True, max_length=120)),
                ("visit_date", models.DateField()),
                ("doctor_name", models.CharField(blank=True, max_length=160)),
                ("symptoms", models.TextField(blank=True)),
                ("extracted_text", models.TextField(blank=True)),
                ("extraction_status", models.CharField(blank=True, max_length=260)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("patient", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="documents", to="records.patient")),
            ],
            options={"ordering": ["-visit_date", "-created_at"]},
        ),
        migrations.CreateModel(
            name="Medicine",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=260)),
                ("raw_line", models.TextField()),
                ("dosage", models.CharField(blank=True, max_length=120)),
                ("frequency", models.CharField(blank=True, max_length=120)),
                ("duration", models.CharField(blank=True, max_length=120)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("document", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="medicines", to="records.document")),
            ],
            options={"ordering": ["id"]},
        ),
    ]
