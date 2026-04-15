from fastapi import APIRouter, Query
from typing import Optional
from services.scoring import compute_rankings, get_filter_options

router = APIRouter()


@router.get("/funds")
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


@router.get("/filters")
def get_filters():
    return get_filter_options()
