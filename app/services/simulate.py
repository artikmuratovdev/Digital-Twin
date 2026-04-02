from __future__ import annotations

from .predict import predict_risk


def simulate_patient_state(
    original_state: dict[str, float],
    updated_state: dict[str, float],
) -> dict[str, float | str]:
    original_result = predict_risk(original_state)
    updated_result = predict_risk(updated_state)

    difference = round(
        float(updated_result["score_percent"]) - float(original_result["score_percent"]),
        2,
    )

    return {
        "old_risk_percent": original_result["score_percent"],
        "new_risk_percent": updated_result["score_percent"],
        "difference_percent": difference,
        "old_risk_level": original_result["risk_level"],
        "new_risk_level": updated_result["risk_level"],
    }