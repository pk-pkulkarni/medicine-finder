from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("records", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="medicine",
            name="quantity",
            field=models.CharField(blank=True, max_length=120),
        ),
    ]
