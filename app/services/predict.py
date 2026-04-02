from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]
MODEL_PATH = BASE_DIR / "models" / "model.pkl"

FEATURE_LABELS = {
    "Glucose": "Glyukoza",
    "BloodPressure": "Qon bosimi",
    "SkinThickness": "Teri osti yog'lari",
    "Insulin": "Insulin",
    "BMI": "BMI",
    "DiabetesPedigreeFunction": "Irsiy moyillik ko'rsatkichi",
    "Age": "Yosh",
}

ZERO_FIXED_COLUMNS = {"Glucose", "BloodPressure", "SkinThickness", "Insulin", "BMI"}
MODEL_NOT_READY_MESSAGE = "Model hali tayyor emas. Avval training scriptni ishga tushiring."

_bundle_cache = None


class ModelNotReadyError(Exception):
    pass


class InvalidPayloadError(Exception):
    pass


def _load_bundle() -> dict:
    global _bundle_cache
    if _bundle_cache is None:
        if not MODEL_PATH.exists():
            raise ModelNotReadyError(MODEL_NOT_READY_MESSAGE)
        _bundle_cache = joblib.load(MODEL_PATH)
    return _bundle_cache


def get_feature_order() -> list[str]:
    return list(_load_bundle()["feature_order"])


def get_feature_labels() -> dict[str, str]:
    return FEATURE_LABELS


def get_model():
    return _load_bundle()["model"]


def get_medians() -> dict[str, float]:
    return dict(_load_bundle()["medians"])


def get_clip_bounds() -> dict[str, dict[str, float]]:
    return dict(_load_bundle().get("clip_bounds", {}))


def validate_payload(payload: dict[str, float]) -> None:
    required = set(get_feature_order())
    provided = set(payload.keys())

    missing = sorted(required - provided)
    if missing:
        raise InvalidPayloadError(f"Payloadda kerakli maydonlar yo'q: {', '.join(missing)}")

    # Extra maydonlar ruxsat, chunki ignore qilinadi


def normalize_payload(payload: dict[str, float]) -> dict[str, float]:
    validate_payload(payload)

    medians = get_medians()
    clip_bounds = get_clip_bounds()
    normalized: dict[str, float] = {}

    for feature in get_feature_order():
        value = float(payload[feature])

        if feature in ZERO_FIXED_COLUMNS and value == 0:
            value = float(medians[feature])

        if feature in clip_bounds:
            lower = float(clip_bounds[feature]["lower"])
            upper = float(clip_bounds[feature]["upper"])
            value = min(max(value, lower), upper)

        normalized[feature] = value

    return normalized


def build_feature_frame(payload: dict[str, float]) -> pd.DataFrame:
    normalized = normalize_payload(payload)
    feature_order = get_feature_order()
    return pd.DataFrame([[normalized[name] for name in feature_order]], columns=feature_order)


def get_risk_level(probability: float) -> str:
    if probability <= 0.30:
        return "Past"
    if probability <= 0.60:
        return "O'rta"
    return "Yuqori"


def predict_risk(payload: dict[str, float]) -> dict[str, float | str | dict[str, float]]:
    model = get_model()
    frame = build_feature_frame(payload)
    probability = float(model.predict_proba(frame)[0][1])

    return {
        "probability": probability,
        "score_percent": round(probability * 100, 2),
        "risk_level": get_risk_level(probability),
        "normalized_payload": {k: float(v) for k, v in frame.iloc[0].to_dict().items()},
    }


def patient_to_payload(patient) -> dict[str, float]:
    payload = {
        "Glucose": float(patient.glucose),
        "BloodPressure": float(patient.blood_pressure),
        "SkinThickness": float(patient.skin_thickness),
        "Insulin": float(patient.insulin),
        "BMI": float(patient.bmi),
        "DiabetesPedigreeFunction": float(patient.pedigree),
        "Age": float(patient.age),
    }

    # faqat model ishlatadigan featurelar qoladi
    return {feature: payload[feature] for feature in get_feature_order()}
