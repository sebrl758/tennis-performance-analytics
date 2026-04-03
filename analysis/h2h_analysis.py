"""
Head-to-head records: opponents with 2+ matches, Win% bar chart.
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
OUT_PATH = ROOT / "outputs" / "charts" / "h2h_analysis.png"

GREEN = "#2e7d32"
RED = "#c62828"
GREY = "#757575"


def normalize_h2h(df: pd.DataFrame) -> pd.DataFrame:
    """Fix Excel title row stored as first data row."""
    df = df.copy()
    if str(df.iloc[0, 0]).strip().lower() == "opponent":
        df.columns = df.iloc[0].values
        df = df.iloc[1:].reset_index(drop=True)
    df.columns = [str(c).strip() for c in df.columns]
    return df


def parse_win_pct(val) -> float | None:
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return None
    s = str(val).strip().replace("%", "")
    if s in ("", "-", "nan"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def to_int(val) -> int | None:
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return None
    try:
        return int(float(str(val).strip()))
    except (ValueError, TypeError):
        return None


def load_h2h(conn: sqlite3.Connection) -> pd.DataFrame:
    raw = pd.read_sql("SELECT * FROM h2h", conn)
    return normalize_h2h(raw)


def bar_color(win_pct: float) -> str:
    if win_pct >= 60:
        return GREEN
    if win_pct <= 40:
        return RED
    return GREY


def main() -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    try:
        df = load_h2h(conn)
    finally:
        conn.close()

    mcol = "Matches" if "Matches" in df.columns else None
    wcol = "W" if "W" in df.columns else None
    lcol = "L" if "L" in df.columns else None
    opp_col = "Opponent" if "Opponent" in df.columns else df.columns[0]
    win_col = "Win%" if "Win%" in df.columns else None

    if not all([mcol, wcol, lcol, win_col]):
        raise RuntimeError("h2h table missing expected columns (Matches, W, L, Win%).")

    df = df.copy()
    df["_m"] = df[mcol].map(to_int)
    df["_w"] = df[wcol].map(to_int)
    df["_l"] = df[lcol].map(to_int)
    df["_win_pct"] = df[win_col].map(parse_win_pct)

    df = df.dropna(subset=["_m", "_w", "_l", "_win_pct"])
    df = df[df["_m"] >= 2]
    df = df.sort_values("_win_pct", ascending=False).reset_index(drop=True)

    if df.empty:
        raise RuntimeError("No opponents with at least 2 matches after filtering.")

    n = len(df)
    heights = df["_win_pct"].to_numpy()
    colors = [bar_color(float(h)) for h in heights]
    labels = [f"{int(w)}-{int(l)}" for w, l in zip(df["_w"], df["_l"])]
    opponents = df[opp_col].astype(str).tolist()

    fig_h = max(6.0, 0.38 * n + 2.0)
    fig, ax = plt.subplots(figsize=(10, fig_h))

    y = np.arange(n)
    bars = ax.barh(y, heights, color=colors, edgecolor="white", linewidth=0.6, height=0.72)

    ax.set_yticks(y)
    ax.set_yticklabels(opponents, fontsize=9)
    ax.invert_yaxis()

    xmax = max(105.0, float(np.nanmax(heights)) * 1.08)
    ax.set_xlim(0, xmax)
    ax.set_xlabel("Win %")
    ax.set_title("Learner Tien — Head-to-Head Records", fontsize=13, fontweight="bold", pad=12)

    for bar, rec, h in zip(bars, labels, heights):
        x = bar.get_width()
        yc = bar.get_y() + bar.get_height() / 2
        ax.text(
            x + 0.8,
            yc,
            rec,
            va="center",
            ha="left",
            fontsize=9,
            color="#333333",
        )

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="x", linestyle="-", linewidth=0.5, color="#e0e0e0", alpha=1.0)
    ax.set_axisbelow(True)

    fig.tight_layout()
    fig.savefig(OUT_PATH, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
