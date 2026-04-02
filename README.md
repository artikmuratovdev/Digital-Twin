# Digital Twin for Diabetes

Digital Twin for Diabetes is a Django hackathon MVP for Type 2 diabetes risk prediction, patient-state simulation, SHAP explainability, patient history tracking, and an Uzbek local assistant powered from the backend.

## Stack

- Django
- SQLite
- XGBoost
- SHAP
- matplotlib
- pandas
- scikit-learn
- Chart.js

## Features

- Type 2 diabetes risk prediction
- Digital Twin simulation for before/after scenarios
- SHAP-based top risk factors
- Patient history storage for glucose and BMI
- History visualization with Chart.js
- Uzbek local summary and local chat
- Clear warning that the system is not a diagnosis tool

## Project Structure

```text
digital_twin_diabetes/
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── manage.py
├── data/
│   └── diabetes.csv
├── models/
│   └── model.pkl   # created after training
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
└── app/
    ├── __init__.py
    ├── admin.py
    ├── apps.py
    ├── models.py
    ├── forms.py
    ├── views.py
    ├── urls.py
    ├── tests.py
    ├── migrations/
    │   └── __init__.py
    ├── services/
    │   ├── __init__.py
    │   ├── preprocess.py
    │   ├── train.py
    │   ├── predict.py
    │   ├── simulate.py
    │   ├── explain.py
    │   ├── ai_summary.py
    │   └── ai_chat.py
    ├── templates/
    │   └── app/
    │       ├── index.html
    │       ├── result.html
    │       ├── simulation.html
    │       └── chat.html
    └── static/
        └── app/
            ├── css/
            │   └── style.css
            ├── js/
            │   ├── chart.js
            │   └── main.js
            └── img/
```

## Local Setup

### 1. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. Install packages

```powershell
pip install -r requirements.txt
```

### 3. Add environment variables

Copy `.env.example` values into your shell or create a local `.env` file for your own reference. The project reads from environment variables:

```powershell
$env:DJANGO_SECRET_KEY="dev-secret-key"
$env:DJANGO_DEBUG="1"
```

## Database Setup

Run migrations before starting the server:

```powershell
python manage.py makemigrations
python manage.py migrate
```

## Train the Model

`models/model.pkl` is not included by default.

Before training, inspect the dataset visually:

```powershell
python app/services/analyze_data.py
```

This command saves matplotlib charts and a summary report into `reports/eda/`.

You must train the model before using prediction, simulation, and SHAP explainability features:

```powershell
python app/services/train.py
```

This command:

- loads `data/diabetes.csv`
- preprocesses the dataset
- trains an XGBoost classifier
- evaluates Accuracy and ROC-AUC
- creates the `models/` directory if needed
- saves the trained bundle to `models/model.pkl`

If `models/model.pkl` does not exist, the web app will show this user-friendly message:

`Model hali tayyor emas. Avval training scriptni ishga tushiring.`

## Run the Django Server

```powershell
python manage.py runserver
```

Open:

`http://127.0.0.1:8000/`

## Notes

- AI outputs are in Uzbek
- The assistant works fully locally and uses patient data, prediction result, SHAP factors, and patient history
- The app does not replace a doctor
- Every AI response includes the warning:

`Bu tashxis emas, faqat xavf baholash natijasi.`
