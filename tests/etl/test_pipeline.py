import json
import sqlite3

import pandas as pd
import pytest

from src.etl.config import PROCESSED_COLUMNS, RAW_COLUMNS
from src.etl.pipeline import run_etl
from src.etl.transform import DataValidationError, transform_data


def make_raw_data() -> pd.DataFrame:
    first = {
        "crim": 0.01, "zn": 18.0, "indus": 2.3, "chas": 0,
        "nox": 0.53, "rm": 6.5, "age": 65.0, "dis": 4.1,
        "rad": 1, "tax": 296, "ptratio": 15.3, "b": 396.9,
        "lstat": 4.9, "medv": 24.0,
    }
    second = {**first, "rm": 7.1, "medv": 31.5}
    return pd.DataFrame([first, second, first], columns=RAW_COLUMNS)


def test_transform_validates_and_prepares_data():
    processed, report = transform_data(make_raw_data())

    assert list(processed.columns) == list(PROCESSED_COLUMNS)
    assert len(processed) == 2
    assert report.duplicate_rows_removed == 1
    assert processed.loc[0, "price_usd"] == pytest.approx(24_000)
    assert "b" not in processed.columns
    assert "medv" not in processed.columns


def test_transform_rejects_missing_required_column():
    raw = make_raw_data().drop(columns="rm")

    with pytest.raises(DataValidationError, match="rm"):
        transform_data(raw)


def test_pipeline_writes_csv_database_and_report(tmp_path):
    raw_path = tmp_path / "raw.csv"
    processed_path = tmp_path / "processed.csv"
    database_path = tmp_path / "openhousing.db"
    report_path = tmp_path / "quality.json"
    make_raw_data().to_csv(raw_path, index=False)

    report = run_etl(raw_path, processed_path, database_path, report_path)

    assert report["status"] == "success"
    assert report["output_rows"] == 2
    assert processed_path.exists()
    assert database_path.exists()
    assert json.loads(report_path.read_text(encoding="utf-8"))["output_rows"] == 2

    with sqlite3.connect(database_path) as connection:
        row_count = connection.execute("SELECT COUNT(*) FROM housing").fetchone()[0]
        columns = {
            row[1] for row in connection.execute("PRAGMA table_info(housing)").fetchall()
        }
    assert row_count == 2
    assert columns == set(PROCESSED_COLUMNS)
