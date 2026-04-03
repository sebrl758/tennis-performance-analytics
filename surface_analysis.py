"""
Surface-level aggregates from matches (+ RPW% from career splits when missing in match log).
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Writable font cache when default MPL config dir is unavailable (CI/sandbox).
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".matplotlib"))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DB_PATH = ROOT / "tien_database.db"
OUT_PATH = ROOT / "outputs" / "charts" / "surface_analysis.png"

SURFACES = ["Hard", "Clay", "Grass"]
COLORS = {"Hard": "#001f3f", "Clay": "#D2691E", "Grass": "#228B22"}


def normalize_matches(df: pd.DataFrame) -> pd.DataFrame:
    """Fix Excel title row stored as first data row (matches table)."""
    df = df.copy()
    if str(df.iloc[0, 0]).strip() == "Date":
        df.columns = df.iloc[0].values
        df = df.iloc[1:].reset_index(drop=True)
    df.columns = [str(c).strip() for c in df.columns]
    return df


def normalize_splits(df: pd.DataFrame) -> pd.DataFrame:
    """Fix Excel title row in splits table."""
    df = df.copy()
    if str(df.iloc[0, 0]).strip() == "Split":
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


def load_surface_rpw_from_splits(conn: sqlite3.Connection) -> pd.Series:
    """RPW% by surface from Career Splits (match log has no per-match RPW%)."""
    raw = pd.read_sql("SELECT * FROM splits", conn)
    sp = normalize_splits(raw)
    if "Split" not in sp.columns or "RPW" not in sp.columns:
        return pd.Series(dtype=float)
    surf = sp[sp["Split"].isin(SURFACES)].copy()
    surf["RPW_pct"] = surf["RPW"].map(parse_pct)
    return surf.set_index("Split")["RPW_pct"]


def aggregate_by_surface(df: pd.DataFrame) -> tuple[pd.DataFrame, bool]:
    """Returns (aggregates, any_non_null_rpw_in_match_rows)."""
    m = df[df["Result"].isin(["W", "L"])].copy()
    m["Surface"] = m["Surface"].astype(str).str.strip()
    m = m[m["Surface"].isin(SURFACES)]

    m["win"] = (m["Result"] == "W").astype(float)
    m["DR_f"] = m["DR"].map(parse_dr)
    m["1stW_pct"] = m["1stW%"].map(parse_pct)
    m["2ndW_pct"] = m["2ndW%"].map(parse_pct)
    if "RPW%" in m.columns:
        m["RPW_pct"] = m["RPW%"].map(parse_pct)
    else:
        m["RPW_pct"] = np.nan
    rpw_from_matches = m["RPW_pct"].notna().any()

    rows = []
    for s in SURFACES:
        g = m[m["Surface"] == s]
        n = len(g)
        wr = 100.0 * g["win"].mean() if n else np.nan
        dr = g["DR_f"].mean(skipna=True)
        f1 = g["1stW_pct"].mean(skipna=True)
        f2 = g["2ndW_pct"].mean(skipna=True)
        rpw = g["RPW_pct"].mean(skipna=True) if rpw_from_matches else np.nan
        rows.append(
            {
                "Surface": s,
                "win_rate": wr,
                "DR": dr,
                "1stW_pct": f1,
                "2ndW_pct": f2,
                "RPW_pct": rpw,
                "n_matches": n,
            }
        )
    return pd.DataFrame(rows), rpw_from_matches


def bar_labels(ax, rects, fmt: str) -> None:
    for r in rects:
        h = r.get_height()
        if np.isnan(h):
            continue
        ax.annotate(
            fmt.format(h),
            xy=(r.get_x() + r.get_width() / 2, h),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9,
        )


def main() -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    try:
        matches = load_matches(conn)
        agg, rpw_from_matches = aggregate_by_surface(matches)
        rpw_split = load_surface_rpw_from_splits(conn)
    finally:
        conn.close()

    use_match_rpw = rpw_from_matches and agg["RPW_pct"].notna().any()
    if use_match_rpw:
        rpw_series = agg.set_index("Surface")["RPW_pct"]
    else:
        rpw_vals = []
        for s in SURFACES:
            if s in rpw_split.index and not np.isnan(rpw_split[s]):
                rpw_vals.append(rpw_split[s])
            else:
                rpw_vals.append(np.nan)
        rpw_series = pd.Series(rpw_vals, index=SURFACES)

    x = np.arange(len(SURFACES))
    width = 0.65
    colors = [COLORS[s] for s in SURFACES]

    fig, axes = plt.subplots(2, 2, figsize=(11, 9))
    fig.suptitle("Learner Tien — Performance by Surface", fontsize=14, fontweight="bold")

    # (0,0) Win rate
    ax = axes[0, 0]
    rects = ax.bar(x, agg["win_rate"], width, color=colors, edgecolor="white", linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(SURFACES)
    ax.set_ylabel("Win rate (%)")
    ax.set_ylim(0, max(100, np.nanmax(agg["win_rate"]) * 1.15) if agg["win_rate"].notna().any() else 100)
    ax.set_title("Win rate")
    bar_labels(ax, rects, "{:.1f}%")

    # (0,1) DR
    ax = axes[0, 1]
    rects = ax.bar(x, agg["DR"], width, color=colors, edgecolor="white", linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(SURFACES)
    ax.set_ylabel("Average DR")
    ax.set_title("Dominance ratio (match avg.)")
    ymax = np.nanmax(agg["DR"]) * 1.2 if agg["DR"].notna().any() else 1.5
    ax.set_ylim(0, max(ymax, 0.5))
    bar_labels(ax, rects, "{:.2f}")

    # (1,0) 1stW% + 2ndW% grouped
    ax = axes[1, 0]
    w = 0.35
    r1 = ax.bar(x - w / 2, agg["1stW_pct"], w, label="1stW%", color=colors, edgecolor="white", linewidth=0.6)
    r2 = ax.bar(x + w / 2, agg["2ndW_pct"], w, label="2ndW%", color=colors, alpha=0.65, edgecolor="white", linewidth=0.6)
    ax.set_xticks(x)
    ax.set_xticklabels(SURFACES)
    ax.set_ylabel("%")
    ax.set_title("Serve won — 1st & 2nd")
    ax.legend(loc="upper right")
    ax.set_ylim(0, 100)
    bar_labels(ax, r1, "{:.1f}%")
    bar_labels(ax, r2, "{:.1f}%")

    # (1,1) RPW% — from career splits (not in match-level log)
    ax = axes[1, 1]
    rects = ax.bar(x, rpw_series.values, width, color=colors, edgecolor="white", linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(SURFACES)
    ax.set_ylabel("RPW (%)")
    ax.set_title("Return points won %")
    ax.set_ylim(0, max(55, np.nanmax(rpw_series.values) * 1.15))
    bar_labels(ax, rects, "{:.1f}%")
    rpw_note = (
        "RPW%: match-level averages from Match Log."
        if use_match_rpw
        else "RPW%: career tour-level surface splits (Match Log has no per-match RPW%)."
    )
    ax.text(
        0.5,
        -0.18,
        rpw_note,
        transform=ax.transAxes,
        ha="center",
        fontsize=8,
        style="italic",
        color="#444444",
    )

    plt.tight_layout(rect=[0, 0.02, 1, 0.96])
    fig.savefig(OUT_PATH, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
