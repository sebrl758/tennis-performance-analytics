"""
Year-end ATP ranking trajectory from the rankings table.
"""

from __future__ import annotations

import os
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".matplotlib"))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DB_PATH = ROOT / "tien_database.db"
OUT_PATH = ROOT / "outputs" / "charts" / "ranking_trajectory.png"

NAVY = "#001f3f"


def normalize_rankings(df: pd.DataFrame) -> pd.DataFrame:
    """Fix Excel title row stored as first data row."""
    df = df.copy()
    if str(df.iloc[0, 0]).strip().lower().startswith("year"):
        df.columns = df.iloc[0].values
        df = df.iloc[1:].reset_index(drop=True)
    df.columns = [str(c).strip() for c in df.columns]
    return df


def parse_year(val) -> int | None:
    s = str(val).strip()
    m = re.match(r"^(\d{4})", s)
    return int(m.group(1)) if m else None


def parse_rank(val) -> float | None:
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return None
    s = str(val).strip().replace("~", "").replace(",", "")
    s = re.sub(r"[^\d.]", "", s)
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def load_rankings(conn: sqlite3.Connection) -> pd.DataFrame:
    raw = pd.read_sql("SELECT * FROM rankings", conn)
    return normalize_rankings(raw)


def main() -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    try:
        df = load_rankings(conn)
    finally:
        conn.close()

    year_col = "Year" if "Year" in df.columns else df.columns[0]
    rank_col = next(
        (c for c in df.columns if "year" in c.lower() and "end" in c.lower()),
        None,
    )
    if rank_col is None:
        rank_col = df.columns[1]

    years = []
    ranks = []
    for _, row in df.iterrows():
        y = parse_year(row[year_col])
        r = parse_rank(row[rank_col])
        if y is None or r is None:
            continue
        if 2022 <= y <= 2026:
            years.append(y)
            ranks.append(r)

    if len(years) < 2:
        raise RuntimeError("Not enough year-end rank rows for 2022–2026.")

    years = np.array(years, dtype=float)
    ranks = np.array(ranks, dtype=float)

    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.size": 10,
            "axes.edgecolor": "#cccccc",
            "axes.linewidth": 0.8,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
        }
    )

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(
        years,
        ranks,
        color=NAVY,
        linewidth=2,
        marker="o",
        markersize=7,
        markerfacecolor=NAVY,
        markeredgecolor="white",
        markeredgewidth=1.2,
    )

    ax.invert_yaxis()
    ax.set_xlabel("Year")
    ax.set_ylabel("ATP rank (year-end)")
    ax.set_title("Learner Tien — ATP Ranking Trajectory", fontsize=13, fontweight="bold", pad=12)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", linestyle="-", linewidth=0.5, color="#e8e8e8", alpha=1.0)
    ax.set_axisbelow(True)

    ax.set_xticks([2022, 2023, 2024, 2025, 2026])
    ax.set_xlim(2021.5, 2026.5)

    ymax = float(np.max(ranks))
    ymin = float(np.min(ranks))
    pad = max(20, (ymax - ymin) * 0.08)
    ax.set_ylim(ymax + pad, max(0, ymin - pad))

    annotations = [
        (2024, "2024 — First Challenger titles", (0, 16)),
        (2025, "2025 — ATP title (Metz)", (0, 28)),
        (2026, "2026 — AO QF, Career High #21", (0, 40)),
    ]

    for yr, text, off in annotations:
        idx = np.where(years == yr)[0]
        if len(idx) == 0:
            continue
        i = int(idx[0])
        x, y = years[i], ranks[i]
        ax.annotate(
            text,
            xy=(x, y),
            xytext=off,
            textcoords="offset points",
            ha="center",
            fontsize=8.5,
            color=NAVY,
            linespacing=1.2,
            bbox=dict(boxstyle="round,pad=0.35", facecolor="white", edgecolor="#e0e0e0", linewidth=0.6),
        )

    fig.tight_layout()
    fig.savefig(OUT_PATH, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
