"""Pencarian diskon/promo dari berbagai sumber."""
from fastapi import APIRouter, Query

from ..services import promo

router = APIRouter(prefix="/api/promos", tags=["promos"])


@router.get("")
def list_promos(
    q: str = Query("", max_length=100, description="Kata kunci produk"),
    sources: str = Query("", description="Pisahkan koma: tracked,affiliate,web (kosong = semua)"),
):
    chosen = [s.strip() for s in sources.split(",") if s.strip()] or None
    return promo.search(q, chosen)


@router.get("/status")
def promo_status(usage: bool = Query(False, description="Sertakan sisa kredit Piloterr (1 panggilan)")):
    return promo.status(include_usage=usage)
