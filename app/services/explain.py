from __future__ import annotations

import shap

from .predict import build_feature_frame, get_feature_labels, get_feature_order, get_model


_explainer_cache = None


def _get_explainer():
    global _explainer_cache
    if _explainer_cache is None:
        _explainer_cache = shap.TreeExplainer(get_model())
    return _explainer_cache


def explain_prediction(payload: dict[str, float], top_n: int = 5) -> list[dict[str, float | str]]:
    frame = build_feature_frame(payload)
    explainer = _get_explainer()
    shap_values = explainer.shap_values(frame)

    # Binary tree model uchun formatlar farq qilishi mumkin
    if isinstance(shap_values, list):
        values = shap_values[1][0]
    else:
        # (1, n_features) shape deb olinadi
        values = shap_values[0]

    labels = get_feature_labels()
    explanations: list[dict[str, float | str]] = []

    for index, feature in enumerate(get_feature_order()):
        signed_impact = float(values[index])
        explanations.append(
            {
                "feature": feature,
                "label": labels.get(feature, feature),
                "value": round(float(frame.iloc[0][feature]), 2),
                "impact": round(abs(signed_impact), 4),
                "signed_impact": round(signed_impact, 4),
                "direction": "xavfni oshiradi" if signed_impact >= 0 else "xavfni kamaytiradi",
            }
        )

    explanations.sort(key=lambda item: float(item["impact"]), reverse=True)
    return explanations[:top_n]