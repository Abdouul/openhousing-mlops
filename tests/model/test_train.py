from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import pytest
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import LinearRegression

from src.etl.config import MODEL_FEATURES
from src.model.train import train_and_select


def make_processed_data(rows: int = 60) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    data = pd.DataFrame({
        "crim": rng.uniform(0, 5, rows),
        "zn": rng.uniform(0, 100, rows),
        "indus": rng.uniform(1, 25, rows),
        "chas": rng.integers(0, 2, rows),
        "nox": rng.uniform(0.4, 0.9, rows),
        "rm": rng.uniform(4, 9, rows),
        "age": rng.uniform(1, 100, rows),
        "dis": rng.uniform(1, 12, rows),
        "rad": rng.integers(1, 25, rows),
        "tax": rng.uniform(180, 700, rows),
        "ptratio": rng.uniform(12, 22, rows),
        "lstat": rng.uniform(1, 35, rows),
    })
    data["price_usd"] = 5_000 + 4_000 * data["rm"] - 300 * data["lstat"]
    return data


def test_training_selects_and_serializes_best_model(tmp_path: Path):
    processed_path = tmp_path / "processed.csv"
    model_path = tmp_path / "model.pkl"
    metrics_path = tmp_path / "metrics.json"
    make_processed_data().to_csv(processed_path, index=False)

    report = train_and_select(
        processed_path,
        model_path,
        metrics_path,
        estimators={
            "LinearRegression": LinearRegression(),
            "DummyRegressor": DummyRegressor(strategy="mean"),
        },
    )

    assert report["best_model"] == "LinearRegression"
    assert report["comparison"][0]["rmse_usd"] < report["comparison"][1]["rmse_usd"]
    assert model_path.exists()
    assert metrics_path.exists()

    model = joblib.load(model_path)
    assert list(model.feature_names_in_) == list(MODEL_FEATURES)
    prediction = model.predict(make_processed_data(10).loc[:, list(MODEL_FEATURES)])
    assert np.isfinite(prediction).all()


def test_training_rejects_invalid_schema(tmp_path: Path):
    processed_path = tmp_path / "invalid.csv"
    make_processed_data().drop(columns="rm").to_csv(processed_path, index=False)

    with pytest.raises(ValueError, match="rm"):
        train_and_select(processed_path, tmp_path / "model.pkl", tmp_path / "metrics.json")
