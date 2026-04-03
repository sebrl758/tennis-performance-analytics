"""
Win rate by round at ATP tour level (excludes Challenger & ITF).
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".matplotlib"))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DB_PATH = ROOT / "tien_database.db"
OUT_PATH = ROOT / "outputs" / "charts" / "round_analysis.png"

ROUND_ORDER = ["R128", "R64", "R32", "R16", "QF", "SF", "F"]
NAVY = "#001f3f"
QF_RED = "#c62828"


def normalize_matches(df: pd.DataFrame) -> pd.DataFrame:
    """Fix Excel title row stored as first data row (matches table)."""
    df = df.copy()
    if str(df.iloc[0, 0]).strip() == "Date":
        df.columns = df.iloc[0].values
        df = df.iloc[1:].reset_index(drop=True)
    df.columns = [str(c).strip() for c in df.columns]
    return df


def load_matches(conn: sqlite3.Connection) -> pd.DataFrame:
    raw = pd.read_sql("SELECT * FROM matches", conn)
    return normalize_matches(raw)


def main() -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    try:
        df = load_matches(conn)
    finally:
        conn.close()

    df = df[df["Result"].isin(["W", "L"])].copy()
    df["Level"] = df["Level"].astype(str).str.strip()
    # ATP tour level only: drop Challenger and ITF.
    df = df[~df["Level"].isin(["Challenger", "ITF"])]

    df["Round"] = df["Round"].astype(str).str.strip()
    df = df[df["Round"].isin(ROUND_ORDER)]

    # Compute explicitly to avoid any aggregation ambiguity:
    # win_rate(%) = (wins / total_matches) * 100
    g = df.groupby("Round", observed=False)
    wins = g.apply(lambda d: (d["Result"] == "W").sum())
    total = g.size()
    win_rate = (wins / total) * 100.0

    agg = pd.DataFrame({"win_rate": win_rate, "n": total}).reindex(ROUND_ORDER)
    agg = agg.dropna(subset=["win_rate", "n"], how="any")

    rounds = agg.index.tolist()
    if not rounds:
        raise RuntimeError("No tour-level matches in the specified rounds.")

    win_rates = agg["win_rate"].to_numpy(dtype=float)
    counts = agg["n"].to_numpy(dtype=int)
    colors = [QF_RED if r == "QF" else NAVY for r in rounds]

    x = np.arange(len(rounds))
    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.bar(x, win_rates, color=colors, edgecolor="white", linewidth=0.8, width=0.65)

    ax.set_xticks(x)
    ax.set_xticklabels(rounds)
    ax.set_ylabel("Win rate (%)")
    ax.set_ylim(0, max(100, float(np.nanmax(win_rates)) * 1.15))
    ax.set_title(
        "Learner Tien — Win Rate by Round (Tour Level)",
        fontsize=13,
        fontweight="bold",
        pad=12,
    )

    for bar, win, n in zip(bars, win_rates, counts):
        h = bar.get_height()
        ax.annotate(
            f"{win:.1f}%\nn={n}",
            xy=(bar.get_x() + bar.get_width() / 2, h),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9,
            color="#333333",
        )

    ax.grid(axis="y", linestyle="-", linewidth=0.5, color="#e8e8e8", alpha=1.0)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.tight_layout()
    fig.savefig(OUT_PATH, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
