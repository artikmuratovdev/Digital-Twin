from django.contrib import admin

from .models import Patient, PatientHistory, SimulationResult


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("id", "glucose", "bmi", "age", "created_at")
    search_fields = ("id",)
    ordering = ("-created_at",)


@admin.register(PatientHistory)
class PatientHistoryAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "date", "glucose", "bmi")
    list_filter = ("date",)
    ordering = ("-date", "-id")


@admin.register(SimulationResult)
class SimulationResultAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "old_risk", "new_risk", "difference", "created_at")
    ordering = ("-created_at",)

