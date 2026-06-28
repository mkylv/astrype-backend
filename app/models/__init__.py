"""Paylaşılan pydantic şemaları."""
from datetime import date, time
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class BirthData(BaseModel):
    """Astro hesaplamaları için doğum bilgisi."""

    birth_date: date
    birth_time: Optional[time] = None
    birth_time_known: bool = True
    lat: float
    lng: float
    tz: str = "UTC"
    place: Optional[str] = None


class ProfileIn(BaseModel):
    display_name: Optional[str] = None
    birth_date: Optional[date] = None
    birth_time: Optional[time] = None
    birth_time_known: bool = True
    birth_lat: Optional[float] = None
    birth_lng: Optional[float] = None
    birth_place: Optional[str] = None
    birth_tz: Optional[str] = None
    language: str = "en"
    interests: list[str] = Field(default_factory=list)
    gender: Optional[str] = None
    relationship_status: Optional[str] = None
    work_status: Optional[str] = None


class ChartRequest(BaseModel):
    # Body opsiyonel: profilde doğum bilgisi varsa oradan da alınabilir.
    birth: Optional[BirthData] = None


class TarotPullRequest(BaseModel):
    question: Optional[str] = None


class TarotSpreadRequest(BaseModel):
    question: Optional[str] = None
    spread: Literal["three_card"] = "three_card"


class RelationshipRequest(BaseModel):
    partner_name: Optional[str] = None
    partner_birth: BirthData


class ChatRequest(BaseModel):
    message: str


class NumerologyRequest(BaseModel):
    # İkisi de opsiyonel: profilde varsa oradan, yoksa body'den alınır.
    full_name: Optional[str] = None
    birth_date: Optional[date] = None


class AIResult(BaseModel):
    """OpenAI yorum çıktısı için ortak zarf."""

    content: dict[str, Any]
