from fastapi import APIRouter, Query
from typing import Optional
from scoring import compute_rankings, get_filter_options
from models import RankedFund, FilterOptions

router = APIRouter()


@router.get("/funds", response_model=list[RankedFund])
def get_funds(
    asset_class: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None),
    sort_dir: str = Query("desc"),
):
    return compute_rankings(
        asset_class_filter=asset_class,
        category_filter=category,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )


@router.get("/filters", response_model=FilterOptions)
def get_filters():
    return get_filter_options()
