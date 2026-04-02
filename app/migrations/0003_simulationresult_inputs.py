from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0002_remove_patient_pregnancies"),
    ]

    operations = [
        migrations.AddField(
            model_name="simulationresult",
            name="age",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="simulationresult",
            name="blood_pressure",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="simulationresult",
            name="bmi",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="simulationresult",
            name="glucose",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="simulationresult",
            name="insulin",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="simulationresult",
            name="skin_thickness",
            field=models.FloatField(blank=True, null=True),
        ),
    ]
