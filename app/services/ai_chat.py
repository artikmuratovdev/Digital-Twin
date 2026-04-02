from __future__ import annotations

WARNING_TEXT = "Bu tashxis emas, faqat xavf baholash natijasi."


def _pick_top_factors(explanations) -> str:
    if not explanations:
        return "asosiy omillar aniq ajralmadi"
    return ", ".join(item["label"] for item in explanations[:3])


def _history_note(history_records: list) -> str:
    if not history_records:
        return "Tarixiy ma'lumot yo'q, shu sabab trendni baholash cheklangan."

    latest = history_records[-1]
    return (
        f"Oxirgi tarixiy yozuv {latest.date:%Y-%m-%d} sanada: "
        f"glyukoza {latest.glucose}, BMI {latest.bmi}."
    )


def _fallback_reply(user_message: str, risk_result, explanations, history_records: list) -> str:
    lowered_message = user_message.lower()
    top_factors = _pick_top_factors(explanations)
    history_note = _history_note(history_records)

    if "nega" in lowered_message or "sabab" in lowered_message:
        guidance = f"Xavfga eng ko'p ta'sir qilgan omillar: {top_factors}."
    elif "nima qil" in lowered_message or "kamaytir" in lowered_message or "pasaytir" in lowered_message:
        guidance = (
            "Riskni kamaytirish uchun glyukoza nazorati, ovqatlanish, vazn va jismoniy faollik bo'yicha "
            "shifokor tavsiyasi asosida reja tuzish foydali bo'lishi mumkin."
        )
    else:
        guidance = (
            "Javob lokal model qoidalari asosida shakllantirildi va mavjud risk, omillar hamda tarixga tayangan."
        )

    return (
        f"Savolingiz: {user_message}. "
        f"Joriy xavf {risk_result['score_percent']}% ({risk_result['risk_level']}). "
        f"{guidance} {history_note} "
        f"Bu ma'lumotlar maslahat xarakterida, aniq tavsiya uchun shifokor bilan maslahat zarur. {WARNING_TEXT}"
    )


def generate_ai_chat_reply(patient, risk_result, explanations, history_records, user_message: str) -> str:
    records = list(history_records)
    return _fallback_reply(user_message, risk_result, explanations, records)
