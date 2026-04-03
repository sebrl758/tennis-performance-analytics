"""
Serve statistics by match result (W vs L) from the Match Log.
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
OUT_PATH = ROOT / "outputs" / "charts" / "serve_analysis.png"

NAVY = "#001f3f"
RED = "#c62828"

STAT_COLS = ["Ace%", "DF%", "1stIn%", "1stW%", "2ndW%"]
STAT_LABELS = ["Ace%", "DF%", "1st In%", "1st Won%", "2nd Won%"]


def normalize_matches(df: pd.DataFrame) -> pd.DataFrame:
    """Fix Excel title row stored as first data row (matches table)."""
    df = df.copy()
    if str(df.iloc[0, 0]).strip() == "Date":
        df.columns = df.iloc[0].values
        df = df.iloc[1:].reset_index(drop=True)
    df.columns = [str(c).strip() for c in df.columns]
    return df


def parse_pct(val) -> float:
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return np.nan
    s = str(val).strip()
    if s in ("", "None", "nan", "-"):
        return np.nan
    s = s.replace("%", "").strip()
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
    for c in STAT_COLS:
        if c not in df.columns:
            raise RuntimeError(f"matches table missing column: {c}")
        df[c] = df[c].map(parse_pct)

    grp = df.groupby("Result", observed=True)[STAT_COLS].mean()
    if "W" not in grp.index or "L" not in grp.index:
        raise RuntimeError("Need both W and L rows after grouping.")

    win = grp.loc["W"].to_numpy(dtype=float)
    loss = grp.loc["L"].to_numpy(dtype=float)

    x = np.arange(len(STAT_COLS))
    w = 0.36

    fig, ax = plt.subplots(figsize=(10, 5.5))
    r1 = ax.bar(x - w / 2, win, w, label="Wins", color=NAVY, edgecolor="white", linewidth=0.7)
    r2 = ax.bar(x + w / 2, loss, w, label="Losses", color=RED, edgecolor="white", linewidth=0.7)

    def label_bars(rects, vals: np.ndarray) -> None:
        for rect, v in zip(rects, vals):
            if np.isnan(v):
                continue
            h = rect.get_height()
            ax.annotate(
                f"{v:.1f}%",
                xy=(rect.get_x() + rect.get_width() / 2, h),
                xytext=(0, 3),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=8,
            )

    label_bars(r1, win)
    label_bars(r2, loss)

    ax.set_xticks(x)
    ax.set_xticklabels(STAT_LABELS)
    ax.set_ylabel("%")
    ax.set_ylim(0, max(np.nanmax(win), np.nanmax(loss)) * 1.18)
    ax.set_title("Learner Tien — Serve Stats: Wins vs Losses", fontsize=13, fontweight="bold", pad=12)
    ax.legend(loc="upper right")
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
