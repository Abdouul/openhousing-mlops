"""Entrainement reproductible et selection du modele OpenHousing."""

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping

import joblib
import pandas as pd
import sklearn
import xgboost
from sklearn.base import RegressorMixin
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from xgboost import XGBRegressor

from src.etl.config import MODEL_FEATURES, PROCESSED_DATA_PATH, PROJECT_ROOT

MODEL_PATH = PROJECT_ROOT / "models" / "model.pkl"
METRICS_PATH = PROJECT_ROOT / "models" / "metrics.json"
TARGET = "price_usd"
RANDOM_STATE = 42


def default_estimators() -> dict[str, RegressorMixin]:
    return {
        "LinearRegression": LinearRegression(),
        "RandomForestRegressor": RandomForestRegressor(
            n_estimators=400,
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),
        "XGBRegressor": XGBRegressor(
            objective="reg:squarederror",
            n_estimators=300,
            learning_rate=0.05,
            max_depth=4,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),
    }


def _sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _load_training_data(processed_path: Path) -> tuple[pd.DataFrame, pd.Series]:
    if not processed_path.exists():
        raise FileNotFoundError(
            f"Donnees traitees introuvables: {processed_path}. "
            "Executez d'abord: python -m src.etl.pipeline"
        )
    data = pd.read_csv(processed_path)
    required = {*MODEL_FEATURES, TARGET}
    missing = sorted(required - set(data.columns))
    if missing:
        raise ValueError("Colonnes d'entrainement absentes: " + ", ".join(missing))

    data = data.dropna(subset=[TARGET]).copy()
    if len(data) < 10:
        raise ValueError("Au moins 10 lignes sont requises pour entrainer le modele.")
    if (data[TARGET] < 0).any():
        raise ValueError("price_usd ne peut pas contenir de valeur negative.")

    features = data.loc[:, list(MODEL_FEATURES)]
    target = data[TARGET]
    return features, target


def train_and_select(
    processed_path: Path = PROCESSED_DATA_PATH,
    model_path: Path = MODEL_PATH,
    metrics_path: Path = METRICS_PATH,
    estimators: Mapping[str, RegressorMixin] | None = None,
) -> dict:
    """Compare les modeles, sauvegarde le meilleur au RMSE et retourne le rapport."""
    processed_path = Path(processed_path)
    model_path = Path(model_path)
    metrics_path = Path(metrics_path)
    features, target = _load_training_data(processed_path)

    x_train, x_test, y_train, y_test = train_test_split(
        features,
        target,
        test_size=0.2,
        random_state=RANDOM_STATE,
    )

    candidates = estimators or default_estimators()
    fitted_models: dict[str, Pipeline] = {}
    comparison: list[dict] = []

    for name, estimator in candidates.items():
        pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("regressor", estimator),
        ])
        pipeline.fit(x_train, y_train)
        predictions = pipeline.predict(x_test)
        comparison.append({
            "model": name,
            "mae_usd": float(mean_absolute_error(y_test, predictions)),
            "rmse_usd": float(mean_squared_error(y_test, predictions) ** 0.5),
            "r2": float(r2_score(y_test, predictions)),
        })
        fitted_models[name] = pipeline

    comparison.sort(key=lambda row: row["rmse_usd"])
    best_name = comparison[0]["model"]
    best_model = fitted_models[best_name]

    model_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_model = model_path.with_suffix(model_path.suffix + ".tmp")
    joblib.dump(best_model, temporary_model)
    os.replace(temporary_model, model_path)

    report = {
        "status": "success",
        "trained_at_utc": datetime.now(timezone.utc).isoformat(),
        "selection_metric": "rmse_usd",
        "best_model": best_name,
        "features": list(MODEL_FEATURES),
        "target": TARGET,
        "training_rows": len(x_train),
        "test_rows": len(x_test),
        "dataset_sha256": _sha256(processed_path),
        "model_sha256": _sha256(model_path),
        "versions": {
            "scikit_learn": sklearn.__version__,
            "xgboost": xgboost.__version__,
        },
        "comparison": comparison,
    }
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_metrics = metrics_path.with_suffix(metrics_path.suffix + ".tmp")
    temporary_metrics.write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    os.replace(temporary_metrics, metrics_path)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Entrainement OpenHousing")
    parser.add_argument("--processed", type=Path, default=PROCESSED_DATA_PATH)
    parser.add_argument("--model", type=Path, default=MODEL_PATH)
    parser.add_argument("--metrics", type=Path, default=METRICS_PATH)
    args = parser.parse_args()
    report = train_and_select(args.processed, args.model, args.metrics)
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
