"""Orchestration de bout en bout du pipeline ETL."""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from .config import (
    DATABASE_PATH,
    PROCESSED_DATA_PATH,
    QUALITY_REPORT_PATH,
    RAW_DATA_PATH,
    TABLE_NAME,
)
from .extract import extract_data
from .load import load_processed_csv, load_sqlite
from .transform import transform_data


def _sha256(path: Path) -> str:
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def run_etl(
    source: Path = RAW_DATA_PATH,
    processed_path: Path = PROCESSED_DATA_PATH,
    database_path: Path = DATABASE_PATH,
    report_path: Path = QUALITY_REPORT_PATH,
    download_if_missing: bool = False,
) -> dict:
    """Execute Extract -> Transform -> Load et retourne le rapport qualite."""
    source = Path(source)
    processed_path = Path(processed_path)
    database_path = Path(database_path)
    report_path = Path(report_path)

    raw_data = extract_data(source, download_if_missing=download_if_missing)
    processed_data, transformation_report = transform_data(raw_data)
    load_processed_csv(processed_data, processed_path)
    load_sqlite(processed_data, database_path, TABLE_NAME)

    report = {
        "status": "success",
        "run_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": str(source.resolve()),
        "source_sha256": _sha256(source),
        "processed_csv": str(processed_path.resolve()),
        "processed_sha256": _sha256(processed_path),
        "database": str(database_path.resolve()),
        "table": TABLE_NAME,
        **transformation_report.to_dict(),
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_report = report_path.with_suffix(report_path.suffix + ".tmp")
    temporary_report.write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    temporary_report.replace(report_path)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Pipeline ETL OpenHousing")
    parser.add_argument("--source", type=Path, default=RAW_DATA_PATH)
    parser.add_argument("--processed", type=Path, default=PROCESSED_DATA_PATH)
    parser.add_argument("--database", type=Path, default=DATABASE_PATH)
    parser.add_argument("--report", type=Path, default=QUALITY_REPORT_PATH)
    parser.add_argument("--download-if-missing", action="store_true")
    args = parser.parse_args()
    report = run_etl(
        source=args.source,
        processed_path=args.processed,
        database_path=args.database,
        report_path=args.report,
        download_if_missing=args.download_if_missing,
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
