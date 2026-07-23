"""Validation et transformation des donnees Boston Housing."""

from dataclasses import dataclass, asdict

import numpy as np
import pandas as pd

from .config import MODEL_FEATURES, PROCESSED_COLUMNS, RAW_COLUMNS


class DataValidationError(ValueError):
    """Erreur levee quand la source ne respecte pas le contrat de donnees."""


@dataclass(frozen=True)
class TransformationReport:
    input_rows: int
    output_rows: int
    duplicate_rows_removed: int
    rows_without_target_removed: int
    missing_features: dict[str, int]

    def to_dict(self) -> dict:
        return asdict(self)


def _validate_schema(data: pd.DataFrame) -> None:
    missing_columns = sorted(set(RAW_COLUMNS) - set(data.columns))
    if missing_columns:
        raise DataValidationError(
            "Colonnes obligatoires absentes: " + ", ".join(missing_columns)
        )
    if data.empty:
        raise DataValidationError("Le dataset ne contient aucune ligne.")


def transform_data(data: pd.DataFrame) -> tuple[pd.DataFrame, TransformationReport]:
    """Valide, deduplique et prepare les donnees sans fuite statistique."""
    _validate_schema(data)
    clean = data.loc[:, list(RAW_COLUMNS)].copy()

    for column in RAW_COLUMNS:
        try:
            clean[column] = pd.to_numeric(clean[column], errors="raise")
        except (TypeError, ValueError) as exc:
            raise DataValidationError(
                f"La colonne {column!r} doit etre numerique."
            ) from exc

    clean = clean.replace([np.inf, -np.inf], np.nan)
    input_rows = len(clean)
    duplicate_rows = int(clean.duplicated().sum())
    clean = clean.drop_duplicates().copy()

    rows_without_target = int(clean["medv"].isna().sum())
    clean = clean.dropna(subset=["medv"]).copy()
    if clean.empty:
        raise DataValidationError("Aucune cible medv exploitable apres validation.")
    if (clean["medv"] < 0).any():
        raise DataValidationError("medv ne peut pas contenir de prix negatifs.")

    # Aucune moyenne/mediane n'est apprise ici: l'imputation reste dans le
    # pipeline ML et sera ajustee uniquement sur le jeu d'entrainement.
    missing_features = {
        column: int(clean[column].isna().sum())
        for column in MODEL_FEATURES
        if clean[column].isna().any()
    }

    clean["price_usd"] = clean["medv"] * 1_000.0
    processed = clean.loc[:, list(PROCESSED_COLUMNS)].reset_index(drop=True)

    report = TransformationReport(
        input_rows=input_rows,
        output_rows=len(processed),
        duplicate_rows_removed=duplicate_rows,
        rows_without_target_removed=rows_without_target,
        missing_features=missing_features,
    )
    return processed, report

