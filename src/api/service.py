"""Chargement et inference du modele immobilier."""

import os
from pathlib import Path
from threading import Lock

import joblib
import numpy as np
import pandas as pd

from src.etl.config import MODEL_FEATURES, PROJECT_ROOT

from .schemas import HousingFeatures

DEFAULT_MODEL_PATH = PROJECT_ROOT / "models" / "model.pkl"


class ModelNotReadyError(RuntimeError):
    """Le modele ne peut pas encore servir de predictions."""


class ModelService:
    def __init__(self, model_path: Path):
        self.model_path = Path(model_path)
        self.model = None
        self.feature_names: tuple[str, ...] = ()
        self.model_name = "unknown"
        self.load_error: str | None = None
        self._predict_lock = Lock()

    @property
    def is_ready(self) -> bool:
        return self.model is not None

    def load(self) -> None:
        if not self.model_path.exists():
            raise FileNotFoundError(f"Modele introuvable: {self.model_path}")
        candidate = joblib.load(self.model_path)
        if not callable(getattr(candidate, "predict", None)):
            raise TypeError("L'artefact ne fournit pas de methode predict().")

        features = tuple(getattr(candidate, "feature_names_in_", MODEL_FEATURES))
        if features != MODEL_FEATURES:
            raise ValueError(
                "Schema du modele incompatible. "
                f"Attendu={list(MODEL_FEATURES)}, recu={list(features)}"
            )

        regressor = getattr(candidate, "named_steps", {}).get("regressor", candidate)
        self.model = candidate
        self.feature_names = features
        self.model_name = type(regressor).__name__
        self.load_error = None

    def predict(self, features: HousingFeatures) -> float:
        if not self.is_ready:
            raise ModelNotReadyError(self.load_error or "Modele non charge")
        frame = pd.DataFrame(
            [[getattr(features, name) for name in self.feature_names]],
            columns=self.feature_names,
        )
        with self._predict_lock:
            prediction = float(self.model.predict(frame)[0])
        if not np.isfinite(prediction):
            raise RuntimeError("Le modele a produit une valeur non finie.")
        return prediction


def configured_model_path() -> Path:
    return Path(os.getenv("OPENHOUSING_MODEL_PATH", str(DEFAULT_MODEL_PATH)))
