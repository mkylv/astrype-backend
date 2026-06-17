"""Route'lar arası ortak yardımcılar."""
from fastapi import HTTPException

from app.db.supabase_client import get_profile
from app.models import BirthData


def birth_from_profile(profile: dict | None) -> BirthData:
    """Profil satırından BirthData üret; eksikse 400."""
    if not profile or not profile.get("birth_date") or profile.get("birth_lat") is None:
        raise HTTPException(
            status_code=400,
            detail="Doğum bilgisi eksik. Önce /profile ile doğum verisini kaydet.",
        )
    return BirthData(
        birth_date=profile["birth_date"],
        birth_time=profile.get("birth_time"),
        birth_time_known=profile.get("birth_time_known", True),
        lat=profile["birth_lat"],
        lng=profile["birth_lng"],
        tz=profile.get("birth_tz") or "UTC",
        place=profile.get("birth_place"),
    )


def resolve_birth(sb, user_id: str, override: BirthData | None) -> BirthData:
    if override is not None:
        return override
    return birth_from_profile(get_profile(sb, user_id))
