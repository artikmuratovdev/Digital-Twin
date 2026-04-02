from django import forms

from .models import Patient, PatientHistory


class NumberInput(forms.NumberInput):
    input_type = "number"


class PatientForm(forms.ModelForm):
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
            "skin_thickness": "Teri qalinligi",
        }
        widgets = {
            "glucose": NumberInput(attrs={"min": 0, "step": "0.1"}),
            "blood_pressure": NumberInput(attrs={"min": 0, "step": "0.1"}),
            "skin_thickness": NumberInput(attrs={"min": 0, "step": "0.1"}),
            "insulin": NumberInput(attrs={"min": 0, "step": "0.1"}),
            "bmi": NumberInput(attrs={"min": 0, "step": "0.1"}),
            "pedigree": NumberInput(attrs={"min": 0, "step": "0.001"}),
            "age": NumberInput(attrs={"min": 1, "step": 1}),
        }


class SimulationForm(forms.Form):
    glucose = forms.FloatField(label="Yangi glyukoza", min_value=0, widget=NumberInput(attrs={"step": "0.1"}))
    blood_pressure = forms.FloatField(
        label="Yangi qon bosimi",
        min_value=0,
        widget=NumberInput(attrs={"step": "0.1"}),
    )
    skin_thickness = forms.FloatField(
        label="Yangi teri qalinligi",
        min_value=0,
        widget=NumberInput(attrs={"step": "0.1"}),
    )
    insulin = forms.FloatField(label="Yangi insulin", min_value=0, widget=NumberInput(attrs={"step": "0.1"}))
    bmi = forms.FloatField(label="Yangi BMI", min_value=0, widget=NumberInput(attrs={"step": "0.1"}))
    age = forms.IntegerField(label="Yangi yosh", min_value=1, widget=NumberInput(attrs={"step": 1}))


class HistoryForm(forms.ModelForm):
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
            "glucose": NumberInput(attrs={"min": 0, "step": "0.1"}),
            "bmi": NumberInput(attrs={"min": 0, "step": "0.1"}),
        }


class AIChatForm(forms.Form):
    message = forms.CharField(
        label="Savolingiz",
        max_length=1000,
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "Masalan: Nega risk yuqori?"}),
    )
