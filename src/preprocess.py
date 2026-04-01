import pandas as pd
import numpy as np


INVALID_ZERO_COLUMNS = [
    "Glucose",
    "BloodPressure",
    "SkinThickness",
    "Insulin",
    "BMI",
]


def load_and_preprocess_data(csv_path: str):
    df = pd.read_csv(csv_path)

    for col in INVALID_ZERO_COLUMNS:
        df[col] = df[col].replace(0, np.nan)
        df[col] = df[col].fillna(df[col].median())

    X = df.drop("Outcome", axis=1)
    y = df["Outcome"]

    return X, y, df


if __name__ == "__main__":
    X, y, df = load_and_preprocess_data("../data/diabetes.csv")
    print(df.head())
    print(X.shape, y.shape)