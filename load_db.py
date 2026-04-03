"""
Load LearnerTien_Database.xlsx sheets into SQLite (tien_database.db).
Run from project root: python Analysis/load_db.py
Or from Analysis/: python load_db.py
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pandas as pd

# Project root = parent of this script's directory (Analysis/)
ROOT = Path(__file__).resolve().parent.parent
DEFAULT_XLSX = ROOT / "LearnerTien_Database.xlsx"
FALLBACK_XLSX = ROOT / "LearnerTien_Database (1).xlsx"
DB_PATH = ROOT / "tien_database.db"

# Sheet names → SQLite tables (project brief)
SHEET_TO_TABLE = {
    "\U0001f4cb Match Log": "matches",
    "\U0001f91d H2H Records": "h2h",
    "\u26a1 Pressure Points": "pressure",
    "\U0001f4c5 Seasonal Splits": "seasons",
    "\U0001f3c6 Notable Events": "events",
    "\U0001f4d0 Career Splits": "splits",
    "\U0001f3af Tactics & Charting": "tactics",
    "\U0001f4c8 Ranking History": "rankings",
}


def _excel_path() -> Path:
    if DEFAULT_XLSX.exists():
        return DEFAULT_XLSX
    if FALLBACK_XLSX.exists():
        return FALLBACK_XLSX
    raise FileNotFoundError(
        f"No Excel file found. Expected {DEFAULT_XLSX} or {FALLBACK_XLSX}"
    )


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except (OSError, ValueError):
            pass

    xlsx = _excel_path()
    print(f"Reading: {xlsx.name}")

    wb = pd.read_excel(xlsx, sheet_name=None, engine="openpyxl")
    conn = sqlite3.connect(DB_PATH)
    missing: list[str] = []

    for sheet, table in SHEET_TO_TABLE.items():
        if sheet not in wb:
            missing.append(sheet)
            continue
        df = wb[sheet]
        n = len(df)
        df.to_sql(table, conn, if_exists="replace", index=False)
        print(f"  Loaded -> {table}: {n} rows")

    conn.close()

    if missing:
        print("\nMissing sheets (skipped):", file=sys.stderr)
        for s in missing:
            print(f"  - {s!r}", file=sys.stderr)
        sys.exit(1)

    print(f"\nDatabase ready: {DB_PATH}")


if __name__ == "__main__":
    main()
