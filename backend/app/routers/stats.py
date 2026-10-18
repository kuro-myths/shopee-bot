"""Statistics endpoint."""
from fastapi import APIRouter

from ..services.stats import compute_stats

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("")
def get_stats():
    return compute_stats()
