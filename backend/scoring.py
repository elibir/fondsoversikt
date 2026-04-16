import pandas as pd
import numpy as np
import os
from typing import Optional

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

NUMERIC_FUND_COLS = ["expense_ratio_pct", "aum_usd_bn", "dividend_yield_pct"]
NUMERIC_METRIC_COLS = [
    "ytd_return_pct", "return_1y_pct", "return_3y_ann_pct",
    "volatility_1y_pct", "max_drawdown_1y_pct", "expense_ratio_pct",
    "aum_usd_bn", "dividend_yield_pct", "data_completeness_score",
]
COMPLETENESS_FIELDS = ["return_1y_pct", "return_3y_ann_pct", "volatility_1y_pct", "expense_ratio_pct"]


def load_data() -> pd.DataFrame:
    funds = pd.read_csv(os.path.join(DATA_DIR, "funds.csv"))
    metrics = pd.read_csv(os.path.join(DATA_DIR, "fund_metrics.csv"))

    # Fill missing string metadata so downstream str operations don't crash
    STRING_FUND_COLS = ["fund_name", "asset_class", "category"]
    for col in STRING_FUND_COLS:
        if col in funds.columns:
            funds[col] = funds[col].fillna("").astype(str).str.strip()

    # Coerce numeric columns — invalid values become NaN instead of crashing
    for col in NUMERIC_FUND_COLS:
        if col in funds.columns:
            funds[col] = pd.to_numeric(funds[col], errors="coerce")
    for col in NUMERIC_METRIC_COLS:
        if col in metrics.columns:
            metrics[col] = pd.to_numeric(metrics[col], errors="coerce")

    # Drop duplicate columns from funds before merging (metrics is authoritative)
    funds = funds.drop(columns=["expense_ratio_pct", "aum_usd_bn", "dividend_yield_pct"], errors="ignore")

    merged = funds.merge(metrics, on="ticker", how="left")

    # Compute HHI (Herfindahl-Hirschman Index) — lower = more diversified
    sector = pd.read_csv(os.path.join(DATA_DIR, "fund_sector_exposure.csv"))
    sector["weight_pct"] = pd.to_numeric(sector["weight_pct"], errors="coerce")
    hhi = (
        sector.groupby("ticker")
        .apply(lambda g: ((g["weight_pct"] / 100) ** 2).sum())
        .rename("_hhi")
        .reset_index()
    )
    merged = merged.merge(hhi, on="ticker", how="left")

    # Compute Sharpe ratio — (1y return - risk-free rate) / 1y volatility
    RISK_FREE_RATE = 4.5
    has_both = merged["return_1y_pct"].notna() & merged["volatility_1y_pct"].notna() & (merged["volatility_1y_pct"] != 0)
    merged["sharpe_ratio_1y"] = np.where(
        has_both,
        ((merged["return_1y_pct"] - RISK_FREE_RATE) / merged["volatility_1y_pct"]).round(2),
        np.nan,
    )

    # Compute data completeness — use CSV score if available, fall back to fraction of non-null scoring fields
    if "data_completeness_score" in merged.columns:
        merged["_completeness"] = (merged["data_completeness_score"] / 100).fillna(
            merged[COMPLETENESS_FIELDS].notna().mean(axis=1)
        )
    else:
        merged["_completeness"] = merged[COMPLETENESS_FIELDS].notna().mean(axis=1)

    return merged


def normalize(series: pd.Series, invert: bool = False) -> pd.Series:
    """Min-max normalize a series to 0-100. Invert for metrics where lower is better."""
    min_val = series.min()
    max_val = series.max()
    if max_val == min_val:
        return pd.Series([50.0] * len(series), index=series.index)
    normalized = (series - min_val) / (max_val - min_val) * 100
    return (100 - normalized) if invert else normalized



def compute_rankings(
    asset_class_filter: Optional[str] = None,
    category_filter: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_dir: str = "desc",
) -> list[dict]:
    merged = load_data()

    # Apply filters
    if asset_class_filter:
        merged = merged[merged["asset_class"].str.lower() == asset_class_filter.lower()]
    if category_filter:
        merged = merged[merged["category"].str.lower() == category_filter.lower()]

    if merged.empty:
        return []

    # --- Scoring ---
    # prefer 3y annualised return, fall back to 1y
    def best_return(row):
        for col in ["return_3y_ann_pct", "return_1y_pct"]:
            if pd.notna(row.get(col)):
                return row[col]
        return np.nan

    merged["_best_return"] = merged.apply(best_return, axis=1)

    SCORE_FACTORS = {
        "return":          {"col": "_best_return",      "invert": False, "weight": 0.35},
        "risk":            {"col": "volatility_1y_pct", "invert": True,  "weight": 0.30},
        "cost":            {"col": "expense_ratio_pct", "invert": True,  "weight": 0.20},
        "diversification": {"col": "_hhi",              "invert": True,  "weight": 0.15},
    }

    for factor, f in SCORE_FACTORS.items():
        scores = normalize(merged[f["col"]], invert=f["invert"])
        merged[f"_score_{factor}"] = scores.fillna(scores.median())

    merged["total_score"] = sum(
        merged[f"_score_{factor}"] * f["weight"]
        for factor, f in SCORE_FACTORS.items()
    )

    # Sort
    if sort_by == "name":
        merged = merged.sort_values("fund_name", ascending=(sort_dir == "asc"))
    elif sort_by == "return":
        merged = merged.sort_values("_best_return", ascending=(sort_dir == "asc"), na_position="last")
    elif sort_by == "risk":
        merged = merged.sort_values("volatility_1y_pct", ascending=(sort_dir == "asc"), na_position="last")
    elif sort_by == "cost":
        merged = merged.sort_values("expense_ratio_pct", ascending=(sort_dir == "asc"), na_position="last")
    elif sort_by == "diversification":
        merged = merged.sort_values("_hhi", ascending=(sort_dir == "desc"), na_position="last")
    else:
        merged = merged.sort_values("total_score", ascending=(sort_dir == "asc"))

    merged = merged.reset_index(drop=True)

    def get(row, col):
        val = row.get(col)
        return val if pd.notna(val) else None

    results = []
    for i, row in merged.iterrows():
        results.append({
            "rank": i + 1,
            "fund": {
                "ticker": row["ticker"],
                "fund_name": row["fund_name"],
                "asset_class": row["asset_class"],
                "category": row["category"],
            },
            "metrics": {
                "as_of_date": get(row, "as_of_date"),
                "ytd_return_pct": get(row, "ytd_return_pct"),
                "return_1y_pct": get(row, "return_1y_pct"),
                "return_3y_ann_pct": get(row, "return_3y_ann_pct"),
                "volatility_1y_pct": get(row, "volatility_1y_pct"),
                "max_drawdown_1y_pct": get(row, "max_drawdown_1y_pct"),
                "expense_ratio_pct": get(row, "expense_ratio_pct"),
                "aum_usd_bn": get(row, "aum_usd_bn"),
                "dividend_yield_pct": get(row, "dividend_yield_pct"),
                "data_completeness_score": get(row, "data_completeness_score"),
                "sharpe_ratio_1y": get(row, "sharpe_ratio_1y"),
            },
            "total_score": round(float(row["total_score"]), 1),
            "score_breakdown": {
                f"{factor}_score": round(float(row[f"_score_{factor}"]), 1)
                for factor in SCORE_FACTORS
            },
            "data_completeness": round(float(row["_completeness"]), 2),
        })

    return results


def get_filter_options() -> dict:
    merged = load_data()
    return {
        "asset_classes": sorted(merged["asset_class"].dropna().unique().tolist()),
        "categories": sorted(merged["category"].dropna().unique().tolist()),
    }
