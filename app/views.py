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


def _simulation_difference(old_risk: float, new_risk: float) -> float:
    return round(float(old_risk) - float(new_risk), 2)


def _with_display_difference(item: SimulationResult | None) -> SimulationResult | None:
    if item is None:
        return None
    item.display_difference = _simulation_difference(item.old_risk, item.new_risk)
    return item


def _simulation_chart_data(patient: Patient) -> dict:
    items = list(patient.simulations.all()[:10])
    items.reverse()
    return {
        "labels": [item.created_at.strftime("%Y-%m-%d %H:%M") for item in items],
        "old_risk": [float(item.old_risk) for item in items],
        "new_risk": [float(item.new_risk) for item in items],
        "difference": [_simulation_difference(item.old_risk, item.new_risk) for item in items],
    }


def _simulation_records(patient: Patient) -> list[SimulationResult]:
    return [_with_display_difference(item) for item in patient.simulations.all()[:10]]


def _build_dashboard_context(patient: Patient) -> dict:
    latest_simulation = _with_display_difference(patient.simulations.first())
    simulation_initial = {
        "glucose": latest_simulation.glucose if latest_simulation and latest_simulation.glucose is not None else patient.glucose,
        "blood_pressure": latest_simulation.blood_pressure if latest_simulation and latest_simulation.blood_pressure is not None else patient.blood_pressure,
        "skin_thickness": latest_simulation.skin_thickness if latest_simulation and latest_simulation.skin_thickness is not None else patient.skin_thickness,
        "insulin": latest_simulation.insulin if latest_simulation and latest_simulation.insulin is not None else patient.insulin,
        "bmi": latest_simulation.bmi if latest_simulation and latest_simulation.bmi is not None else patient.bmi,
        "age": latest_simulation.age if latest_simulation and latest_simulation.age is not None else patient.age,
    }
    context = {
        "patient": patient,
        "patient_form": PatientForm(instance=patient),
        "simulation_form": SimulationForm(initial=simulation_initial),
        "history_form": HistoryForm(),
        "ai_chat_form": AIChatForm(),
        "history_records": list(patient.history.all()),
        "simulation_records": _simulation_records(patient),
        "simulation_chart_data": _simulation_chart_data(patient),
        "latest_simulation": latest_simulation,
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

    if request.method == "POST":
        form = SimulationForm(request.POST)
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
                glucose=form.cleaned_data["glucose"],
                blood_pressure=form.cleaned_data["blood_pressure"],
                skin_thickness=form.cleaned_data["skin_thickness"],
                insulin=form.cleaned_data["insulin"],
                bmi=form.cleaned_data["bmi"],
                age=form.cleaned_data["age"],
                old_risk=simulation["old_risk_percent"],
                new_risk=simulation["new_risk_percent"],
                difference=simulation["difference_percent"],
            )
            context["latest_simulation"] = _with_display_difference(saved_result)
            context["simulation_data"] = simulation
            context["simulation_records"] = _simulation_records(patient)
            context["simulation_chart_data"] = _simulation_chart_data(patient)
            context["simulation_form"] = SimulationForm(
                initial={
                    "glucose": saved_result.glucose,
                    "blood_pressure": saved_result.blood_pressure,
                    "skin_thickness": saved_result.skin_thickness,
                    "insulin": saved_result.insulin,
                    "bmi": saved_result.bmi,
                    "age": saved_result.age,
                }
            )
        except ModelNotReadyError as exc:
            context["model_ready"] = False
            context["model_error"] = str(exc) or MODEL_NOT_READY_MESSAGE

        if "simulation_form" not in context:
            context["simulation_form"] = form

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
    return redirect(f"{reverse('patient_detail', args=[patient_id])}#simulation-section")


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
