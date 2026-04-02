from __future__ import annotations

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from .forms import AIChatForm, HistoryForm, PatientForm, SimulationForm
from .models import Patient, PatientHistory, SimulationResult
from .services.ai_chat import generate_ai_chat_reply
from .services.ai_summary import generate_ai_summary
from .services.explain import explain_prediction
from .services.predict import ModelNotReadyError, patient_to_payload, predict_risk
from .services.simulate import simulate_patient_state


MODEL_NOT_READY_MESSAGE = "Model hali tayyor emas. Avval training scriptni ishga tushiring."
WARNING_TEXT = "Bu tashxis emas, faqat xavf baholash natijasi."


def _history_chart_data(patient: Patient) -> dict:
    items = list(patient.history.all())
    return {
        "labels": [item.date.strftime("%Y-%m-%d") for item in items],
        "glucose": [item.glucose for item in items],
        "bmi": [item.bmi for item in items],
    }


def _build_dashboard_context(patient: Patient) -> dict:
    context = {
        "patient": patient,
        "patient_form": PatientForm(instance=patient),
        "simulation_form": SimulationForm(
            initial={
                "glucose": patient.glucose,
                "blood_pressure": patient.blood_pressure,
                "skin_thickness": patient.skin_thickness,
                "insulin": patient.insulin,
                "bmi": patient.bmi,
                "age": patient.age,
            }
        ),
        "history_form": HistoryForm(),
        "ai_chat_form": AIChatForm(),
        "history_records": list(patient.history.all()),
        "simulation_records": list(patient.simulations.all()[:10]),
        "chart_data": _history_chart_data(patient),
        "latest_simulation": patient.simulations.first(),
        "warning_text": WARNING_TEXT,
        "model_ready": True,
        "model_error": "",
        "risk_result": None,
        "explanations": [],
        "initial_summary": "Xulosa hali yaratilmagan.",
    }

    try:
        payload = patient_to_payload(patient)
        context["risk_result"] = predict_risk(payload)
        context["explanations"] = explain_prediction(payload, top_n=5)
        context["initial_summary"] = generate_ai_summary(
            patient=patient,
            risk_result=context["risk_result"],
            explanations=context["explanations"],
            history_records=list(patient.history.all()),
        )
    except ModelNotReadyError as exc:
        context["model_ready"] = False
        context["model_error"] = str(exc) or MODEL_NOT_READY_MESSAGE
        context["initial_summary"] = str(exc) or MODEL_NOT_READY_MESSAGE

    return context


def _build_patient_list() -> list[dict]:
    patients = []
    for patient in Patient.objects.all()[:12]:
        item = {
            "patient": patient,
            "detail_url": reverse("patient_detail", args=[patient.id]),
            "risk_result": None,
        }
        try:
            item["risk_result"] = predict_risk(patient_to_payload(patient))
        except ModelNotReadyError:
            item["risk_result"] = None
        patients.append(item)
    return patients


def home_view(request):
    return render(
        request,
        "app/index.html",
        {
            "patients": _build_patient_list(),
            "warning_text": WARNING_TEXT,
        },
    )


def patient_create_view(request):
    return render(
        request,
        "app/patient_form.html",
        {
            "patient_form": PatientForm(),
            "warning_text": WARNING_TEXT,
        },
    )


def patient_detail_view(request, patient_id: int):
    patient = get_object_or_404(Patient, pk=patient_id)
    context = _build_dashboard_context(patient)
    return render(request, "app/result.html", context)


@require_POST
def predict_view(request):
    form = PatientForm(request.POST)
    if not form.is_valid():
        return render(
            request,
            "app/patient_form.html",
            {
                "patient_form": form,
                "warning_text": WARNING_TEXT,
            },
        )

    patient = form.save()
    PatientHistory.objects.create(
        patient=patient,
        date=patient.created_at.date(),
        glucose=patient.glucose,
        bmi=patient.bmi,
    )
    return redirect(f"{reverse('patient_detail', args=[patient.id])}#simulation-section")


@require_POST
def simulate_view(request, patient_id: int):
    patient = get_object_or_404(Patient, pk=patient_id)
    form = SimulationForm(request.POST)
    context = _build_dashboard_context(patient)

    if not form.is_valid():
        context["simulation_form"] = form
        return render(request, "app/result.html", context)

    original_state = patient_to_payload(patient)
    updated_state = {
        "Glucose": form.cleaned_data["glucose"],
        "BloodPressure": form.cleaned_data["blood_pressure"],
        "SkinThickness": form.cleaned_data["skin_thickness"],
        "Insulin": form.cleaned_data["insulin"],
        "BMI": form.cleaned_data["bmi"],
        "DiabetesPedigreeFunction": patient.pedigree,
        "Age": form.cleaned_data["age"],
    }

    try:
        simulation = simulate_patient_state(original_state, updated_state)
        saved_result = SimulationResult.objects.create(
            patient=patient,
            old_risk=simulation["old_risk_percent"],
            new_risk=simulation["new_risk_percent"],
            difference=simulation["difference_percent"],
        )
        context["latest_simulation"] = saved_result
        context["simulation_data"] = simulation
    except ModelNotReadyError as exc:
        context["model_ready"] = False
        context["model_error"] = str(exc) or MODEL_NOT_READY_MESSAGE

    context["simulation_form"] = form
    return render(request, "app/result.html", context)


@require_POST
def add_history_view(request, patient_id: int):
    patient = get_object_or_404(Patient, pk=patient_id)
    form = HistoryForm(request.POST)
    if form.is_valid():
        history = form.save(commit=False)
        history.patient = patient
        history.save()
    return redirect("patient_detail", patient_id=patient.id)


@require_GET
def ai_summary_view(request, patient_id: int):
    patient = get_object_or_404(Patient, pk=patient_id)
    try:
        payload = patient_to_payload(patient)
        risk_result = predict_risk(payload)
        explanations = explain_prediction(payload, top_n=5)
    except ModelNotReadyError as exc:
        return JsonResponse({"summary": str(exc) or MODEL_NOT_READY_MESSAGE})

    summary = generate_ai_summary(
        patient=patient,
        risk_result=risk_result,
        explanations=explanations,
        history_records=list(patient.history.all()),
    )
    return JsonResponse({"summary": summary})


@require_POST
def ai_chat_view(request, patient_id: int):
    patient = get_object_or_404(Patient, pk=patient_id)
    form = AIChatForm(request.POST)
    if not form.is_valid():
        return JsonResponse({"reply": "Savol yuborilmadi."}, status=400)

    try:
        payload = patient_to_payload(patient)
        risk_result = predict_risk(payload)
        explanations = explain_prediction(payload, top_n=5)
    except ModelNotReadyError as exc:
        return JsonResponse({"reply": str(exc) or MODEL_NOT_READY_MESSAGE})

    reply = generate_ai_chat_reply(
        patient=patient,
        risk_result=risk_result,
        explanations=explanations,
        history_records=list(patient.history.all()),
        user_message=form.cleaned_data["message"],
    )
    return JsonResponse({"reply": reply})
