from __future__ import annotations

import json
from math import ceil
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

try:
    from app.services.preprocess import (
        DATA_PATH,
        INVALID_ZERO_COLUMNS,
        REMOVED_FEATURE_COLUMNS,
        apply_preprocessing,
        build_preprocessing_artifacts,
        load_raw_data,
    )
except ImportError:
    from preprocess import (
        DATA_PATH,
        INVALID_ZERO_COLUMNS,
        REMOVED_FEATURE_COLUMNS,
        apply_preprocessing,
        build_preprocessing_artifacts,
        load_raw_data,
    )


BASE_DIR = Path(__file__).resolve().parents[2]
REPORTS_DIR = BASE_DIR / "reports" / "eda"
CLEANED_DATASET_PATH = BASE_DIR / "data" / "diabetes_cleaned.csv"


def _outlier_counts(dataframe: pd.DataFrame) -> dict[str, int]:
    counts: dict[str, int] = {}
    numeric_columns = dataframe.select_dtypes(include=["number"]).columns
    for column in numeric_columns:
        if column in {"Pregnancies", "Outcome"}:
            continue

        series = dataframe[column].dropna()
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        counts[column] = int(((series < lower_bound) | (series > upper_bound)).sum())
    return counts

def _invalid_zero_counts(dataframe: pd.DataFrame) -> dict[str, int]:
    return {
        column: int((dataframe[column] == 0).sum())
        for column in INVALID_ZERO_COLUMNS
        if column in dataframe.columns
    }


def fix_dataset_anomalies(dataframe: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, dict]]:
    artifacts = build_preprocessing_artifacts(dataframe)
    cleaned = apply_preprocessing(dataframe, artifacts)
    return cleaned, artifacts


def _save_distribution_plot(dataframe: pd.DataFrame, output_dir: Path) -> Path:
    features = [
        "Glucose",
        "BloodPressure",
        "SkinThickness",
        "Insulin",
        "BMI",
        "DiabetesPedigreeFunction",
        "Age",
    ]
    available = [feature for feature in features if feature in dataframe.columns]

    cols = 3
    rows = ceil(len(available) / cols)
    figure, axes = plt.subplots(rows, cols, figsize=(15, 4 * rows))
    axes = np.array(axes).reshape(-1)

    for axis, feature in zip(axes, available):
        axis.hist(
            dataframe[feature].dropna(),
            bins=20,
            color="#1769aa",
            edgecolor="white",
            alpha=0.9,
        )
        axis.set_title(feature)
        axis.set_xlabel("Qiymat")
        axis.set_ylabel("Soni")

    for axis in axes[len(available):]:
        axis.axis("off")

    figure.suptitle("Asosiy ko'rsatkichlar taqsimoti", fontsize=16)
    figure.tight_layout()
    path = output_dir / "distributions.png"
    figure.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(figure)
    return path


def _save_boxplot(dataframe: pd.DataFrame, output_dir: Path) -> Path:
    numeric = dataframe.select_dtypes(include=["number"]).drop(columns=["Outcome"], errors="ignore")

    figure, axis = plt.subplots(figsize=(14, 6))
    axis.boxplot(
        [numeric[column].dropna() for column in numeric.columns],
        tick_labels=list(numeric.columns),
        showfliers=True,
    )
    axis.set_title("Anomaliya va tarqalish uchun boxplot")
    axis.set_ylabel("Qiymat")
    axis.tick_params(axis="x", rotation=25)
    figure.tight_layout()

    path = output_dir / "boxplots.png"
    figure.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(figure)
    return path


def _save_correlation_heatmap(dataframe: pd.DataFrame, output_dir: Path) -> Path:
    correlation = dataframe.corr(numeric_only=True)

    figure, axis = plt.subplots(figsize=(9, 7))
    heatmap = axis.imshow(correlation.values, cmap="RdYlBu_r", vmin=-1, vmax=1)
    axis.set_xticks(range(len(correlation.columns)))
    axis.set_yticks(range(len(correlation.columns)))
    axis.set_xticklabels(correlation.columns, rotation=45, ha="right")
    axis.set_yticklabels(correlation.columns)
    axis.set_title("Korrelyatsiya heatmap")
    figure.colorbar(heatmap, ax=axis, fraction=0.046, pad=0.04)
    figure.tight_layout()

    path = output_dir / "correlation_heatmap.png"
    figure.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(figure)
    return path


def _save_quality_plot(dataframe: pd.DataFrame, output_dir: Path) -> Path:
    zero_counts = _invalid_zero_counts(dataframe)
    missing_counts = dataframe.isna().sum().to_dict()
    outlier_counts = _outlier_counts(dataframe)

    labels = list(zero_counts.keys())
    x = np.arange(len(labels))
    width = 0.35

    figure, axis = plt.subplots(figsize=(11, 6))
    axis.bar(
        x - width / 2,
        [zero_counts[label] for label in labels],
        width=width,
        label="Invalid zero",
        color="#c65353",
    )
    axis.bar(
        x + width / 2,
        [missing_counts.get(label, 0) for label in labels],
        width=width,
        label="NaN",
        color="#e6a93d",
    )
    axis.plot(
        x,
        [outlier_counts.get(label, 0) for label in labels],
        marker="o",
        linewidth=2,
        label="Outlier",
        color="#1769aa",
    )
    axis.set_xticks(x)
    axis.set_xticklabels(labels, rotation=20)
    axis.set_ylabel("Soni")
    axis.set_title("Data quality ko'rsatkichlari")
    axis.legend()
    figure.tight_layout()

    path = output_dir / "data_quality.png"
    figure.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(figure)
    return path


def _save_outcome_plot(dataframe: pd.DataFrame, output_dir: Path) -> Path:
    if "Outcome" not in dataframe.columns:
        raise ValueError("Outcome ustuni topilmadi.")

    outcome_counts = dataframe["Outcome"].value_counts().sort_index()
    labels = ["No diabetes", "Diabetes"]

    figure, axis = plt.subplots(figsize=(6, 5))
    axis.bar(labels[: len(outcome_counts)], outcome_counts.values, color=["#14916b", "#c65353"])
    axis.set_title("Outcome balans")
    axis.set_ylabel("Soni")

    for index, value in enumerate(outcome_counts.values):
        axis.text(index, value + 5, str(int(value)), ha="center")

    figure.tight_layout()
    path = output_dir / "outcome_balance.png"
    figure.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(figure)
    return path


def analyze_dataset(csv_path: Path | None = None, output_dir: Path | None = None) -> dict:
    dataset_path = Path(csv_path) if csv_path else DATA_PATH
    report_dir = Path(output_dir) if output_dir else REPORTS_DIR
    report_dir.mkdir(parents=True, exist_ok=True)

    raw_dataframe = load_raw_data(dataset_path)
    raw_feature_view = raw_dataframe.drop(columns=REMOVED_FEATURE_COLUMNS, errors="ignore")

    cleaned_dataframe, artifacts = fix_dataset_anomalies(raw_dataframe)
    cleaned_dataset_path = CLEANED_DATASET_PATH
    cleaned_dataset_path.parent.mkdir(parents=True, exist_ok=True)
    cleaned_dataframe.to_csv(cleaned_dataset_path, index=False)

    zero_counts_before = _invalid_zero_counts(raw_feature_view)
    outlier_counts_before = _outlier_counts(raw_feature_view)
    zero_counts_after = _invalid_zero_counts(cleaned_dataframe)
    outlier_counts_after = _outlier_counts(cleaned_dataframe)

    report = {
        "dataset_path": str(dataset_path),
        "cleaned_dataset_path": str(cleaned_dataset_path),
        "rows": int(len(raw_feature_view)),
        "columns": int(len(raw_feature_view.columns)),
        "duplicate_rows_before_cleaning": int(raw_dataframe.duplicated().sum()),
        "duplicate_rows_after_cleaning": int(cleaned_dataframe.duplicated().sum()),
        "missing_values_before_cleaning": {
            column: int(count)
            for column, count in raw_feature_view.isna().sum().to_dict().items()
        },
        "missing_values_after_cleaning": {
            column: int(count)
            for column, count in cleaned_dataframe.isna().sum().to_dict().items()
        },
        "invalid_zero_values_before_cleaning": zero_counts_before,
        "invalid_zero_values_after_cleaning": zero_counts_after,
        "outlier_counts_before_cleaning": outlier_counts_before,
        "outlier_counts_after_cleaning": outlier_counts_after,
        "preprocessing_artifacts": {
            "filled_with_median": artifacts["medians"],
            "clip_bounds": artifacts["clip_bounds"],
        },
        "plots": {
            "distributions": str(_save_distribution_plot(cleaned_dataframe, report_dir)),
            "boxplots": str(_save_boxplot(cleaned_dataframe, report_dir)),
            "correlation_heatmap": str(_save_correlation_heatmap(cleaned_dataframe, report_dir)),
            "data_quality": str(_save_quality_plot(cleaned_dataframe, report_dir)),
            "outcome_balance": str(_save_outcome_plot(cleaned_dataframe, report_dir)),
        },
    }

    report_path = report_dir / "summary.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    report["summary_path"] = str(report_path)
    return report


def main() -> None:
    report = analyze_dataset()
    print("Dataset tahlili tugadi.")
    print(f"Qatorlar soni: {report['rows']}")
    print(f"Ustunlar soni: {report['columns']}")
    print(f"Duplicate qatorlar (oldin): {report['duplicate_rows_before_cleaning']}")
    print(f"Duplicate qatorlar (keyin): {report['duplicate_rows_after_cleaning']}")
    print("Invalid zero qiymatlar (oldin):")
    for column, count in report["invalid_zero_values_before_cleaning"].items():
        print(f"  - {column}: {count}")
    print("Invalid zero qiymatlar (keyin):")
    for column, count in report["invalid_zero_values_after_cleaning"].items():
        print(f"  - {column}: {count}")
    print("Outlier sonlari (oldin):")
    for column, count in report["outlier_counts_before_cleaning"].items():
        print(f"  - {column}: {count}")
    print("Outlier sonlari (keyin):")
    for column, count in report["outlier_counts_after_cleaning"].items():
        print(f"  - {column}: {count}")
    print(f"Tozalangan dataset: {report['cleaned_dataset_path']}")
    print(f"Hisobot JSON: {report['summary_path']}")
    print("Grafiklar:")
    for name, path in report["plots"].items():
        print(f"  - {name}: {path}")


if __name__ == "__main__":
    main()