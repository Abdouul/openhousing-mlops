"""Chargement des donnees transformees dans CSV et SQLite."""

import os
import sqlite3
from pathlib import Path

import pandas as pd

from .config import DATABASE_PATH, PROCESSED_DATA_PATH, TABLE_NAME


def load_processed_csv(data: pd.DataFrame, destination: Path = PROCESSED_DATA_PATH) -> Path:
    """Ecrit le CSV traite de facon atomique."""
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = destination.with_suffix(destination.suffix + ".tmp")
    data.to_csv(temporary_path, index=False)
    os.replace(temporary_path, destination)
    return destination


def load_sqlite(
    data: pd.DataFrame,
    database_path: Path = DATABASE_PATH,
    table_name: str = TABLE_NAME,
) -> Path:
    """Remplace la table cible dans une transaction SQLite."""
    database_path = Path(database_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(database_path) as connection:
        data.to_sql(table_name, connection, if_exists="replace", index=False)
        connection.execute(
            f"CREATE INDEX IF NOT EXISTS idx_{table_name}_price_usd "
            f"ON {table_name} (price_usd)"
        )
    return database_path
