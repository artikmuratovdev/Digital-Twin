from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

try:
    from app.services.analyze_data import CLEANED_DATASET_PATH, analyze_dataset
except ImportError:
    from analyze_data import CLEANED_DATASET_PATH, analyze_dataset

try:
    from app.services.preprocess import build_preprocessing_artifacts, load_raw_data
except ImportError:
    from preprocess import build_preprocessing_artifacts, load_raw_data


BASE_DIR = Path(__file__).resolve().parents[2]
MODEL_DIR = BASE_DIR / "models"
MODEL_PATH = MODEL_DIR / "model.pkl"
TARGET_COLUMN = "Outcome"


def train_model() -> Path:
    dataset_path = CLEANED_DATASET_PATH
    if not dataset_path.exists():
        analyze_dataset()

    dataframe = pd.read_csv(dataset_path)

    if TARGET_COLUMN not in dataframe.columns:
        raise ValueError(f"Datasetda '{TARGET_COLUMN}' ustuni topilmadi.")

    X = dataframe.drop(columns=[TARGET_COLUMN])
    y = dataframe[TARGET_COLUMN]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    model = XGBClassifier(
        n_estimators=180,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        eval_metric="logloss",
        random_state=42,
    )
    model.fit(X_train, y_train)

    probabilities = model.predict_proba(X_test)[:, 1]
    predictions = model.predict(X_test)

    accuracy = accuracy_score(y_test, predictions)
    roc_auc = roc_auc_score(y_test, probabilities)

    # medians va clip_bounds inferenceda kerak bo'ladi

    raw_df = load_raw_data()
    preprocessing = build_preprocessing_artifacts(raw_df)

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "model": model,
            "feature_order": list(X.columns),
            "medians": preprocessing["medians"],
            "clip_bounds": preprocessing["clip_bounds"],
            "metrics": {
                "accuracy": round(float(accuracy), 4),
                "roc_auc": round(float(roc_auc), 4),
            },
            "training_dataset_path": str(dataset_path),
        },
        MODEL_PATH,
    )

    print(f"Accuracy: {accuracy:.4f}")
    print(f"ROC-AUC: {roc_auc:.4f}")
    print(f"Training dataset: {dataset_path}")
    print(f"Model saqlandi: {MODEL_PATH}")

    saved = joblib.load(MODEL_PATH)
    print("Feature order:", saved["feature_order"])

    return MODEL_PATH


if __name__ == "__main__":
    train_model()