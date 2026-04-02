from __future__ import annotations

WARNING_TEXT = "Bu tashxis emas, faqat xavf baholash natijasi."


def _fallback_summary(risk_result, explanations, history_records: list) -> str:
    top_factors = ", ".join(item["label"] for item in explanations[:3]) or "aniq ustun omillar aniqlanmadi"
    trend_note = "Tarix mavjud." if history_records else "Tarixiy ma'lumot hali kam."
    return (
        f"Joriy xavf {risk_result['score_percent']}% ({risk_result['risk_level']}). "
        f"Asosiy omillar: {top_factors}. {trend_note} "
        f"Xulosa lokal model qoidalari asosida tuzildi. "
        f"Shifokor bilan maslahatlashish tavsiya etiladi. {WARNING_TEXT}"
    )


def generate_ai_summary(patient, risk_result, explanations, history_records) -> str:
    records = list(history_records)
    return _fallback_summary(risk_result, explanations, records)
