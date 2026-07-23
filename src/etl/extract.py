"""Extraction des donnees brutes."""

from pathlib import Path
from urllib.request import urlopen

import pandas as pd

from .config import RAW_DATA_PATH, SOURCE_URL


def download_raw_data(destination: Path = RAW_DATA_PATH, source_url: str = SOURCE_URL) -> Path:
    """Telecharge la source sans la transformer, avec ecriture atomique."""
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = destination.with_suffix(destination.suffix + ".tmp")
    with urlopen(source_url, timeout=30) as response:
        temporary_path.write_bytes(response.read())
    temporary_path.replace(destination)
    return destination


def extract_data(source: Path = RAW_DATA_PATH, download_if_missing: bool = False) -> pd.DataFrame:
    """Lit le CSV brut et retourne une copie en memoire."""
    source = Path(source)
    if not source.exists():
        if not download_if_missing:
            raise FileNotFoundError(
                f"Source introuvable: {source}. Placez BostonHousing.csv dans data/raw "
                "ou utilisez --download-if-missing."
            )
        download_raw_data(source)
    if source.stat().st_size == 0:
        raise ValueError(f"Le fichier source est vide: {source}")
    return pd.read_csv(source)
