import pandas as pd
import numpy as np
import os
from typing import Optional

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    funds = pd.read_csv(os.path.join(DATA_DIR, "funds.csv"))
    metrics = pd.read_csv(os.path.join(DATA_DIR, "fund_metrics.csv"))
    return funds, metrics


def normalize(series: pd.Series, invert: bool = False) -> pd.Series:
    """Min-max normalize a series to 0-100. Invert for metrics where lower is better."""
    min_val = series.min()
    max_val = series.max()
    if max_val == min_val:
        return pd.Series([50.0] * len(series), index=series.index)
    normalized = (series - min_val) / (max_val - min_val) * 100
    return (100 - normalized) if invert else normalized


def score_label(score: float) -> str:
    if score >= 75:
        return "Høy"
    elif score >= 40:
        return "Middels"
    else:
        return "Lav"


def compute_rankings(
    asset_class_filter: Optional[str] = None,
    category_filter: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_dir: str = "desc",
) -> list[dict]:
    funds_df, metrics_df = load_data()

    # Drop columns from funds that also exist in metrics to avoid merge conflicts
    funds_df = funds_df.drop(columns=["expense_ratio_pct", "aum_usd_bn", "dividend_yield_pct"], errors="ignore")

    merged = funds_df.merge(metrics_df, on="ticker", how="left")

    # Apply filters
    if asset_class_filter:
        merged = merged[merged["asset_class"].str.lower() == asset_class_filter.lower()]
    if category_filter:
        merged = merged[merged["category"].str.lower() == category_filter.lower()]

    if merged.empty:
        return []

    # --- Scoring ---
    # Factor 1: Return score (40%) — prefer 3y annualised, fall back to 1y
    def best_return(row):
        for col in ["return_3y_ann_pct", "return_1y_pct"]:
            if pd.notna(row.get(col)):
                return row[col]
        return np.nan

    merged["_best_return"] = merged.apply(best_return, axis=1)

    # Factor 2: Risk score (35%) — lower volatility = better
    # Factor 3: Cost score (25%) — lower expense ratio = better
    score_cols = {
        "return": ("_best_return",       False, 0.40),
        "risk":   ("volatility_1y_pct",  True,  0.35),
        "cost":   ("expense_ratio_pct",  True,  0.25),
    }

    for factor, (col, invert, _) in score_cols.items():
        valid = merged[col].dropna()
        if len(valid) > 0:
            merged[f"_score_{factor}"] = normalize(merged[col], invert=invert)
        else:
            merged[f"_score_{factor}"] = 50.0  # neutral fallback

    merged["total_score"] = (
        merged["_score_return"].fillna(50) * 0.40
        + merged["_score_risk"].fillna(50) * 0.35
        + merged["_score_cost"].fillna(50) * 0.25
    )

    # Data completeness — use CSV score if available, else compute from key metric fields
    metric_fields = ["return_1y_pct", "return_3y_ann_pct", "volatility_1y_pct", "expense_ratio_pct"]
    if "data_completeness_score" in merged.columns:
        merged["_completeness"] = merged["data_completeness_score"] / 100
    else:
        merged["_completeness"] = merged[metric_fields].notna().mean(axis=1)

    # Sort
    if sort_by == "name":
        merged = merged.sort_values("fund_name", ascending=(sort_dir == "asc"))
    elif sort_by == "return":
        merged = merged.sort_values("_best_return", ascending=(sort_dir == "asc"), na_position="last")
    elif sort_by == "risk":
        merged = merged.sort_values("volatility_1y_pct", ascending=(sort_dir == "asc"), na_position="last")
    elif sort_by == "cost":
        merged = merged.sort_values("expense_ratio_pct", ascending=(sort_dir == "asc"), na_position="last")
    else:
        merged = merged.sort_values("total_score", ascending=False)

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
            },
            "total_score": round(float(row["total_score"]), 1),
            "score_breakdown": {
                "return_score": round(float(row["_score_return"]) if pd.notna(row["_score_return"]) else 50, 1),
                "risk_score": round(float(row["_score_risk"]) if pd.notna(row["_score_risk"]) else 50, 1),
                "cost_score": round(float(row["_score_cost"]) if pd.notna(row["_score_cost"]) else 50, 1),
                "label_return": score_label(row["_score_return"] if pd.notna(row["_score_return"]) else 50),
                "label_risk": score_label(row["_score_risk"] if pd.notna(row["_score_risk"]) else 50),
                "label_cost": score_label(row["_score_cost"] if pd.notna(row["_score_cost"]) else 50),
            },
            "data_completeness": round(float(row["_completeness"]), 2),
        })

    return results


def get_filter_options() -> dict:
    funds_df, _ = load_data()
    return {
        "asset_classes": sorted(funds_df["asset_class"].dropna().unique().tolist()),
        "categories": sorted(funds_df["category"].dropna().unique().tolist()),
    }
