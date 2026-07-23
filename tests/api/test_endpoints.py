from pathlib import Path

import joblib
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline

from src.api.main import create_app
from src.etl.config import MODEL_FEATURES


@pytest.fixture
def payload() -> dict:
    return {
        "crim": 0.00632,
        "zn": 18.0,
        "indus": 2.31,
        "chas": 0,
        "nox": 0.538,
        "rm": 6.575,
        "age": 65.2,
        "dis": 4.09,
        "rad": 1,
        "tax": 296.0,
        "ptratio": 15.3,
        "lstat": 4.98,
    }


@pytest.fixture
def model_path(tmp_path: Path, payload: dict) -> Path:
    rows = []
    for offset in (0.0, 0.2, 0.4, 0.6):
        row = payload.copy()
        row["rm"] += offset
        row["lstat"] += offset * 2
        rows.append(row)
    features = pd.DataFrame(rows, columns=MODEL_FEATURES)
    targets = [24_000.0, 26_000.0, 28_000.0, 30_000.0]
    pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("regressor", LinearRegression()),
    ])
    pipeline.fit(features, targets)
    destination = tmp_path / "model.pkl"
    joblib.dump(pipeline, destination)
    return destination


def test_health_readiness_and_model_info(model_path: Path):
    with TestClient(create_app(model_path)) as client:
        health = client.get("/health")
        ready = client.get("/ready")
        model = client.get("/model")

    assert health.status_code == 200
    assert health.json() == {"status": "healthy", "model_loaded": True}
    assert ready.status_code == 200
    assert model.json()["model_name"] == "LinearRegression"
    assert model.json()["features"] == list(MODEL_FEATURES)


def test_predict_returns_usd_price(model_path: Path, payload: dict):
    with TestClient(create_app(model_path)) as client:
        response = client.post("/predict", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["currency"] == "USD"
    assert body["model_name"] == "LinearRegression"
    assert body["estimated_price_usd"] > 0


def test_predict_rejects_invalid_payload(model_path: Path, payload: dict):
    payload["chas"] = 4
    payload["unknown"] = 123
    with TestClient(create_app(model_path)) as client:
        response = client.post("/predict", json=payload)

    assert response.status_code == 422


def test_missing_model_returns_degraded_and_unavailable(tmp_path: Path, payload: dict):
    missing_path = tmp_path / "missing.pkl"
    with TestClient(create_app(missing_path)) as client:
        health = client.get("/health")
        prediction = client.post("/predict", json=payload)

    assert health.json() == {"status": "degraded", "model_loaded": False}
    assert prediction.status_code == 503
