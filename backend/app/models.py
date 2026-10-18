"""Pydantic schemas for the API."""
from typing import Optional

from pydantic import BaseModel, Field


class ProductIn(BaseModel):
    url: str
    name: str = "Untitled product"
    marketplace: str = "unknown"
    image: str = ""
    current_price: Optional[float] = Field(None, ge=0)
    note: str = ""


class ProductOut(BaseModel):
    id: int
    url: str
    name: str
    marketplace: str
    image: str = ""
    current_price: Optional[float] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    target_price: Optional[float] = None
    target_reached: bool = False
    note: str = ""
    archived: bool = False
    created_at: str
    updated_at: str


class HistoryPoint(BaseModel):
    price: float
    date: str


class AffiliateOut(BaseModel):
    url: str
    source: str  # "shopee_api" | "tiktok_api" | "original"
    note: str = ""


class TargetIn(BaseModel):
    target_price: float


class TargetOut(BaseModel):
    id: int
    target_price: Optional[float]
    target_reached: bool


class NoteIn(BaseModel):
    note: str
