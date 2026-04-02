from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_PATH = BASE_DIR / "data" / "diabetes.csv"

INVALID_ZERO_COLUMNS = ["Glucose", "BloodPressure", "SkinThickness", "Insulin", "BMI"]
TARGET_COLUMN = "Outcome"
REMOVED_FEATURE_COLUMNS = ["Pregnancies"]


def load_raw_data(csv_path: Path | None = None) -> pd.DataFrame:
    dataset_path = Path(csv_path) if csv_path else DATA_PATH
    return pd.read_csv(dataset_path)


def _compute_clip_bounds(dataframe: pd.DataFrame) -> dict[str, dict[str, float]]:
    bounds: dict[str, dict[str, float]] = {}

    numeric_columns = dataframe.select_dtypes(include=["number"]).columns
    for column in numeric_columns:
        if column == TARGET_COLUMN:
            continue

        series = dataframe[column].dropna()
        q1 = float(series.quantile(0.25))
        q3 = float(series.quantile(0.75))
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        bounds[column] = {"lower": lower, "upper": upper}

    return bounds


def build_preprocessing_artifacts(dataframe: pd.DataFrame) -> dict[str, dict]:
    cleaned = dataframe.drop_duplicates().copy()
    cleaned = cleaned.drop(columns=REMOVED_FEATURE_COLUMNS, errors="ignore")

    for column in INVALID_ZERO_COLUMNS:
        if column in cleaned.columns:
            cleaned[column] = cleaned[column].replace(0, np.nan)

    feature_frame = cleaned.drop(columns=[TARGET_COLUMN], errors="ignore")
    medians = {
        column: float(value)
        for column, value in feature_frame.median(numeric_only=True).to_dict().items()
    }
    clip_bounds = _compute_clip_bounds(feature_frame)

    return {
        "medians": medians,
        "clip_bounds": clip_bounds,
    }


def apply_preprocessing(dataframe: pd.DataFrame, artifacts: dict[str, dict]) -> pd.DataFrame:
    processed = dataframe.drop_duplicates().copy()
    processed = processed.drop(columns=REMOVED_FEATURE_COLUMNS, errors="ignore")

    medians = artifacts["medians"]
    clip_bounds = artifacts["clip_bounds"]

    for column in INVALID_ZERO_COLUMNS:
        if column in processed.columns:
            processed[column] = processed[column].replace(0, np.nan)

    for column, median in medians.items():
        if column in processed.columns:
            processed[column] = processed[column].fillna(median)

    for column, bounds in clip_bounds.items():
        if column in processed.columns:
            processed[column] = processed[column].clip(
                lower=bounds["lower"],
                upper=bounds["upper"],
            )

    return processed


def load_and_preprocess_data(csv_path: Path | None = None):
    raw_dataframe = load_raw_data(csv_path)

    if TARGET_COLUMN not in raw_dataframe.columns:
        raise ValueError(f"Datasetda '{TARGET_COLUMN}' ustuni topilmadi.")

    artifacts = build_preprocessing_artifacts(raw_dataframe)
    dataframe = apply_preprocessing(raw_dataframe, artifacts)

    X = dataframe.drop(columns=[TARGET_COLUMN])
    y = dataframe[TARGET_COLUMN]
    return X, y, artifacts