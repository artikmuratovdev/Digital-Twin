from django.test import TestCase
from django.urls import reverse

from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd
from .models import Patient, PatientHistory, SimulationResult
from .services.analyze_data import analyze_dataset
from .services.ai_chat import generate_ai_chat_reply
from .services.ai_summary import generate_ai_summary
from .services.preprocess import apply_preprocessing, build_preprocessing_artifacts


class SmokeTests(TestCase):
    def test_home_page_loads(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bemorlar boshqaruvi")

    def test_home_page_lists_saved_patients(self):
        patient = Patient.objects.create(
            glucose=111,
            blood_pressure=72,
            skin_thickness=20,
            insulin=84,
            bmi=27.9,
            pedigree=0.41,
            age=34,
        )
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f"#{patient.id}")
        self.assertContains(response, reverse("patient_detail", args=[patient.id]))

    def test_patient_create_page_loads(self):
        response = self.client.get(reverse("patient_create"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Yangi bemor ma'lumotlari")

    def test_predict_redirects_to_patient_simulation_section(self):
        response = self.client.post(
            reverse("predict"),
            {
                "glucose": 118,
                "blood_pressure": 74,
                "skin_thickness": 22,
                "insulin": 86,
                "bmi": 28.4,
                "pedigree": 0.43,
                "age": 35,
            },
        )
        patient = Patient.objects.latest("id")
        self.assertRedirects(
            response,
            f"{reverse('patient_detail', args=[patient.id])}#simulation-section",
            fetch_redirect_response=False,
        )

    def test_patient_detail_renders_initial_summary(self):
        patient = Patient.objects.create(
            glucose=118,
            blood_pressure=74,
            skin_thickness=22,
            insulin=86,
            bmi=28.4,
            pedigree=0.43,
            age=35,
        )
        PatientHistory.objects.create(patient=patient, date="2026-04-01", glucose=115, bmi=28.1)
        response = self.client.get(reverse("patient_detail", args=[patient.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Xulosa lokal model qoidalari asosida tuzildi.")

    def test_patient_detail_shows_simulation_history_table(self):
        patient = Patient.objects.create(
            glucose=118,
            blood_pressure=74,
            skin_thickness=22,
            insulin=86,
            bmi=28.4,
            pedigree=0.43,
            age=35,
        )
        SimulationResult.objects.create(patient=patient, old_risk=12.4, new_risk=10.1, difference=-2.3)
        SimulationResult.objects.create(patient=patient, old_risk=10.1, new_risk=9.6, difference=-0.5)
        response = self.client.get(reverse("patient_detail", args=[patient.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Simulyatsiyalar tarixi")
        self.assertContains(response, "12,40%")
        self.assertContains(response, "9,60%")
        self.assertContains(response, 'id="simulation-section"', html=False)

    def test_patient_detail_prefills_simulation_form_from_latest_simulation(self):
        patient = Patient.objects.create(
            glucose=118,
            blood_pressure=74,
            skin_thickness=22,
            insulin=86,
            bmi=28.4,
            pedigree=0.43,
            age=35,
        )
        SimulationResult.objects.create(
            patient=patient,
            glucose=109,
            blood_pressure=70,
            skin_thickness=19,
            insulin=77,
            bmi=25.9,
            age=33,
            old_risk=12.4,
            new_risk=10.1,
            difference=-2.3,
        )
        response = self.client.get(reverse("patient_detail", args=[patient.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="109.0"', html=False)
        self.assertContains(response, 'value="70.0"', html=False)
        self.assertContains(response, 'value="19.0"', html=False)
        self.assertContains(response, 'value="77.0"', html=False)
        self.assertContains(response, 'value="25.9"', html=False)
        self.assertContains(response, 'value="33"', html=False)

    def test_patient_detail_handles_simulation_post_without_url_change(self):
        patient = Patient.objects.create(
            glucose=118,
            blood_pressure=74,
            skin_thickness=22,
            insulin=86,
            bmi=28.4,
            pedigree=0.43,
            age=35,
        )
        response = self.client.post(
            reverse("patient_detail", args=[patient.id]),
            {
                "glucose": 110,
                "blood_pressure": 72,
                "skin_thickness": 20,
                "insulin": 80,
                "bmi": 26.8,
                "age": 34,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "So'nggi simulyatsiya natijasi")
        self.assertEqual(SimulationResult.objects.filter(patient=patient).count(), 1)
        saved_result = SimulationResult.objects.get(patient=patient)
        self.assertEqual(saved_result.glucose, 110)
        self.assertEqual(saved_result.blood_pressure, 72)
        self.assertEqual(saved_result.skin_thickness, 20)
        self.assertEqual(saved_result.insulin, 80)
        self.assertEqual(saved_result.bmi, 26.8)
        self.assertEqual(saved_result.age, 34)
        self.assertContains(response, f"{saved_result.old_risk:.2f}%".replace(".", ","))
        self.assertContains(response, f"{saved_result.new_risk:.2f}%".replace(".", ","))

    def test_local_ai_summary_uses_rule_based_response(self):
        patient = Patient.objects.create(
            glucose=145,
            blood_pressure=82,
            skin_thickness=25,
            insulin=120,
            bmi=31.4,
            pedigree=0.52,
            age=43,
        )
        PatientHistory.objects.create(patient=patient, date="2026-04-01", glucose=140, bmi=30.9)
        summary = generate_ai_summary(
            patient=patient,
            risk_result={"score_percent": 68, "risk_level": "Yuqori"},
            explanations=[
                {"label": "Glyukoza", "value": 145, "signed_impact": "+0.42", "direction": "oshirdi"},
                {"label": "BMI", "value": 31.4, "signed_impact": "+0.21", "direction": "oshirdi"},
            ],
            history_records=list(patient.history.all()),
        )
        self.assertIn("Joriy xavf 68% (Yuqori).", summary)
        self.assertIn("lokal model qoidalari", summary)

    def test_local_ai_chat_returns_rule_based_reply(self):
        patient = Patient.objects.create(
            glucose=160,
            blood_pressure=88,
            skin_thickness=24,
            insulin=130,
            bmi=33.2,
            pedigree=0.61,
            age=47,
        )
        PatientHistory.objects.create(patient=patient, date="2026-03-30", glucose=155, bmi=32.8)
        reply = generate_ai_chat_reply(
            patient=patient,
            risk_result={"score_percent": 74, "risk_level": "Yuqori"},
            explanations=[
                {"label": "Glyukoza", "value": 160, "signed_impact": "+0.45", "direction": "oshirdi"},
                {"label": "BMI", "value": 33.2, "signed_impact": "+0.20", "direction": "oshirdi"},
            ],
            history_records=list(patient.history.all()),
            user_message="Nega risk yuqori chiqdi?",
        )
        self.assertIn("Xavfga eng ko'p ta'sir qilgan omillar", reply)
        self.assertIn("Bu tashxis emas", reply)

    def test_dataset_analysis_generates_matplotlib_outputs(self):
        with TemporaryDirectory() as temp_dir:
            report = analyze_dataset(output_dir=Path(temp_dir))

            self.assertIn("plots", report)
            self.assertTrue(Path(report["summary_path"]).exists())
            self.assertTrue(Path(report["plots"]["distributions"]).exists())
            self.assertTrue(Path(report["plots"]["boxplots"]).exists())
            self.assertTrue(Path(report["plots"]["correlation_heatmap"]).exists())

    def test_preprocessing_fixes_invalid_zero_and_caps_outlier(self):
        dataframe = pd.DataFrame(
            [
                {
                    "Glucose": 110,
                    "BloodPressure": 68,
                    "SkinThickness": 18,
                    "Insulin": 80,
                    "BMI": 27.0,
                    "DiabetesPedigreeFunction": 0.35,
                    "Age": 29,
                    "Outcome": 0,
                },
                {
                    "Glucose": 120,
                    "BloodPressure": 70,
                    "SkinThickness": 20,
                    "Insulin": 85,
                    "BMI": 28.0,
                    "DiabetesPedigreeFunction": 0.4,
                    "Age": 33,
                    "Outcome": 0,
                },
                {
                    "Glucose": 130,
                    "BloodPressure": 75,
                    "SkinThickness": 22,
                    "Insulin": 90,
                    "BMI": 29.0,
                    "DiabetesPedigreeFunction": 0.5,
                    "Age": 37,
                    "Outcome": 1,
                },
                {
                    "Glucose": 0,
                    "BloodPressure": 80,
                    "SkinThickness": 24,
                    "Insulin": 0,
                    "BMI": 31.0,
                    "DiabetesPedigreeFunction": 0.6,
                    "Age": 40,
                    "Outcome": 1,
                },
                {
                    "Glucose": 125,
                    "BloodPressure": 72,
                    "SkinThickness": 21,
                    "Insulin": 88,
                    "BMI": 28.5,
                    "DiabetesPedigreeFunction": 0.45,
                    "Age": 35,
                    "Outcome": 0,
                },
                {
                    "Glucose": 128,
                    "BloodPressure": 74,
                    "SkinThickness": 23,
                    "Insulin": 92,
                    "BMI": 29.4,
                    "DiabetesPedigreeFunction": 0.48,
                    "Age": 36,
                    "Outcome": 0,
                },
                {
                    "Glucose": 400,
                    "BloodPressure": 200,
                    "SkinThickness": 60,
                    "Insulin": 900,
                    "BMI": 55.0,
                    "DiabetesPedigreeFunction": 2.1,
                    "Age": 79,
                    "Outcome": 1,
                },
            ]
        )

        artifacts = build_preprocessing_artifacts(dataframe)
        processed = apply_preprocessing(dataframe, artifacts)

        self.assertNotEqual(processed.loc[2, "Glucose"], 0)
        self.assertNotEqual(processed.loc[2, "Insulin"], 0)
        self.assertLess(processed.loc[5, "Glucose"], 400)
        self.assertLess(processed.loc[5, "Insulin"], 900)
