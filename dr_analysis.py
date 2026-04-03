"""
Dominance ratio (DR) distribution for wins vs losses from the Match Log.
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
OUT_PATH = ROOT / "outputs" / "charts" / "dr_analysis.png"


def normalize_matches(df: pd.DataFrame) -> pd.DataFrame:
    """Fix Excel title row stored as first data row (matches table)."""
    df = df.copy()
    if str(df.iloc[0, 0]).strip() == "Date":
        df.columns = df.iloc[0].values
        df = df.iloc[1:].reset_index(drop=True)
    df.columns = [str(c).strip() for c in df.columns]
    return df


def parse_dr(val) -> float:
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return np.nan
    s = str(val).strip()
    if s in ("", "None", "nan", "-", "Live"):
        return np.nan
    try:
        return float(s)
    except ValueError:
        return np.nan


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
    df["DR_f"] = df["DR"].map(parse_dr)
    df = df.dropna(subset=["DR_f"])

    wins = df[df["Result"] == "W"]["DR_f"].to_numpy()
    losses = df[df["Result"] == "L"]["DR_f"].to_numpy()

    mean_w = float(np.mean(wins)) if len(wins) else float("nan")
    mean_l = float(np.mean(losses)) if len(losses) else float("nan")

    fig, ax = plt.subplots(figsize=(9, 5.5))
    n_bins = 16
    combined = np.concatenate([wins, losses]) if len(wins) or len(losses) else np.array([])
    if len(combined):
        lo, hi = float(np.min(combined)), float(np.max(combined))
        if lo == hi:
            lo, hi = lo - 0.05, hi + 0.05
        bin_edges = np.linspace(lo, hi, n_bins + 1)
    else:
        bin_edges = n_bins

    ax.hist(
        wins,
        bins=bin_edges,
        alpha=0.6,
        color="green",
        label=f"Wins (n={len(wins)})",
    )
    ax.hist(
        losses,
        bins=bin_edges,
        alpha=0.6,
        color="red",
        label=f"Losses (n={len(losses)})",
    )

    ax.axvline(1.0, color="black", linestyle="--", linewidth=1.2, label="DR = 1.0")

    ax.set_title("Dominance Ratio Distribution — Wins vs Losses", fontsize=13, fontweight="bold")
    ax.set_xlabel("Dominance ratio (DR)")
    ax.set_ylabel("Count")
    ax.legend(loc="upper right")

    note = f"Mean DR (wins): {mean_w:.3f}\nMean DR (losses): {mean_l:.3f}"
    ax.text(
        0.02,
        0.98,
        note,
        transform=ax.transAxes,
        fontsize=11,
        verticalalignment="top",
        bbox=dict(boxstyle="round", facecolor="white", edgecolor="#cccccc", alpha=0.9),
    )

    fig.tight_layout()
    fig.savefig(OUT_PATH, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
