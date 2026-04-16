from pydantic import BaseModel
from typing import Optional


class FundBase(BaseModel):
    ticker: str
    fund_name: str
    asset_class: str
    category: str


class FundMetrics(BaseModel):
    as_of_date: Optional[str] = None
    ytd_return_pct: Optional[float] = None
    return_1y_pct: Optional[float] = None
    return_3y_ann_pct: Optional[float] = None
    volatility_1y_pct: Optional[float] = None
    max_drawdown_1y_pct: Optional[float] = None
    expense_ratio_pct: Optional[float] = None
    aum_usd_bn: Optional[float] = None
    dividend_yield_pct: Optional[float] = None
    data_completeness_score: Optional[int] = None
    sharpe_ratio_1y: Optional[float] = None


class ScoreBreakdown(BaseModel):
    return_score: Optional[float] = None
    risk_score: Optional[float] = None
    cost_score: Optional[float] = None
    diversification_score: Optional[float] = None


class RankedFund(BaseModel):
    rank: int
    fund: FundBase
    metrics: FundMetrics
    total_score: float
    score_breakdown: ScoreBreakdown
    missing_factors: list[str]


class FilterOptions(BaseModel):
    asset_classes: list[str]
    categories: list[str]
