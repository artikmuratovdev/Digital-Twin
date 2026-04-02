from django.db import models


class Patient(models.Model):
    glucose = models.FloatField()
    blood_pressure = models.FloatField()
    skin_thickness = models.FloatField()
    insulin = models.FloatField()
    bmi = models.FloatField()
    pedigree = models.FloatField()
    age = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        return f"Bemor #{self.pk}"


class PatientHistory(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="history")
    date = models.DateField()
    glucose = models.FloatField()
    bmi = models.FloatField()

    class Meta:
        ordering = ["date", "id"]

    def __str__(self) -> str:
        return f"Tarix #{self.pk} - Bemor #{self.patient_id}"


class SimulationResult(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="simulations")
    old_risk = models.FloatField()
    new_risk = models.FloatField()
    difference = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        return f"Simulyatsiya #{self.pk} - Bemor #{self.patient_id}"
