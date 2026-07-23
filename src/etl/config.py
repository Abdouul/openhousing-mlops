"""Configuration centralisee du pipeline ETL OpenHousing."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "BostonHousing.csv"
PROCESSED_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "boston_housing_clean.csv"
DATABASE_PATH = PROJECT_ROOT / "database" / "openhousing.db"
QUALITY_REPORT_PATH = PROJECT_ROOT / "data" / "processed" / "quality_report.json"
TABLE_NAME = "housing"
SOURCE_URL = "https://raw.githubusercontent.com/selva86/datasets/master/BostonHousing.csv"

RAW_COLUMNS = (
    "crim", "zn", "indus", "chas", "nox", "rm", "age", "dis",
    "rad", "tax", "ptratio", "b", "lstat", "medv",
)
MODEL_FEATURES = tuple(column for column in RAW_COLUMNS if column not in {"b", "medv"})
PROCESSED_COLUMNS = (*MODEL_FEATURES, "price_usd")
