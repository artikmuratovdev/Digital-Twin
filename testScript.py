from app.services.explain import explain_prediction

payload = {
    "Glucose": 135,
    "BloodPressure": 80,
    "SkinThickness": 30,
    "Insulin": 112.9,
    "BMI": 31.0,
    "DiabetesPedigreeFunction": 0.6,
    "Age": 40
}

result = explain_prediction(payload)
for item in result:
    print(item)