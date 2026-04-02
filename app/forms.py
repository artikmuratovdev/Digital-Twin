from django import forms

from .models import Patient, PatientHistory


FIELD_LIMITS = {
    "glucose": {"min": 1, "max": 300, "step": "0.1"},
    "blood_pressure": {"min": 1, "max": 200, "step": "0.1"},
    "skin_thickness": {"min": 1, "max": 100, "step": "0.1"},
    "insulin": {"min": 1, "max": 900, "step": "0.1"},
    "bmi": {"min": 1, "max": 70, "step": "0.1"},
    "pedigree": {"min": 0.001, "max": 3, "step": "0.001"},
    "age": {"min": 1, "max": 120, "step": 1},
}


class NumberInput(forms.NumberInput):
    input_type = "number"

    def __init__(self, attrs=None):
        base_attrs = {
            "inputmode": "decimal",
            "autocomplete": "off",
            "data-numeric-strict": "true",
        }
        if attrs:
            base_attrs.update(attrs)
        super().__init__(attrs=base_attrs)


class PatientForm(forms.ModelForm):
    glucose = forms.FloatField(min_value=1, max_value=300, widget=NumberInput(attrs=FIELD_LIMITS["glucose"]))
    blood_pressure = forms.FloatField(
        min_value=1,
        max_value=200,
        widget=NumberInput(attrs=FIELD_LIMITS["blood_pressure"]),
    )
    skin_thickness = forms.FloatField(
        min_value=1,
        max_value=100,
        widget=NumberInput(attrs=FIELD_LIMITS["skin_thickness"]),
    )
    insulin = forms.FloatField(min_value=1, max_value=900, widget=NumberInput(attrs=FIELD_LIMITS["insulin"]))
    bmi = forms.FloatField(min_value=1, max_value=70, widget=NumberInput(attrs=FIELD_LIMITS["bmi"]))
    pedigree = forms.FloatField(min_value=0.001, max_value=3, widget=NumberInput(attrs=FIELD_LIMITS["pedigree"]))
    age = forms.IntegerField(min_value=1, max_value=120, widget=NumberInput(attrs=FIELD_LIMITS["age"]))

    class Meta:
        model = Patient
        fields = [
            "glucose",
            "blood_pressure",
            "skin_thickness",
            "insulin",
            "bmi",
            "pedigree",
            "age",
        ]
        labels = {
            "glucose": "Glyukoza",
            "blood_pressure": "Qon bosimi",
            "insulin": "Insulin",
            "bmi": "BMI",
            "pedigree": "Diabetga irsiy moyillik ko'rsatkichi",
            "age": "Yosh",
            "skin_thickness": "Teri osti yog'lari",
        }


class SimulationForm(forms.Form):
    glucose = forms.FloatField(
        label="Yangi glyukoza",
        min_value=1,
        max_value=300,
        widget=NumberInput(attrs=FIELD_LIMITS["glucose"]),
    )
    blood_pressure = forms.FloatField(
        label="Yangi qon bosimi",
        min_value=1,
        max_value=200,
        widget=NumberInput(attrs=FIELD_LIMITS["blood_pressure"]),
    )
    skin_thickness = forms.FloatField(
        label="Yangi teri osti yog'lari",
        min_value=1,
        max_value=100,
        widget=NumberInput(attrs=FIELD_LIMITS["skin_thickness"]),
    )
    insulin = forms.FloatField(
        label="Yangi insulin",
        min_value=1,
        max_value=900,
        widget=NumberInput(attrs=FIELD_LIMITS["insulin"]),
    )
    bmi = forms.FloatField(label="Yangi BMI", min_value=1, max_value=70, widget=NumberInput(attrs=FIELD_LIMITS["bmi"]))
    age = forms.IntegerField(label="Yangi yosh", min_value=1, max_value=120, widget=NumberInput(attrs=FIELD_LIMITS["age"]))


class HistoryForm(forms.ModelForm):
    glucose = forms.FloatField(min_value=1, max_value=300, widget=NumberInput(attrs=FIELD_LIMITS["glucose"]))
    bmi = forms.FloatField(min_value=1, max_value=70, widget=NumberInput(attrs=FIELD_LIMITS["bmi"]))

    class Meta:
        model = PatientHistory
        fields = ["date", "glucose", "bmi"]
        labels = {
            "date": "Sana",
            "glucose": "Glyukoza",
            "bmi": "BMI",
        }
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
        }


class AIChatForm(forms.Form):
    message = forms.CharField(
        label="Savolingiz",
        max_length=1000,
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "Masalan: Nega risk yuqori?"}),
    )
