"""Auth bağımlılığı — Supabase JWT doğrular, current_user döner."""
from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException, status
from jose import JWTError, jwt

from app.config import Settings, get_settings
from app.db.supabase_client import get_supabase, get_user_tier


@dataclass
class CurrentUser:
    id: str
    email: str | None = None


def _decode_token(token: str, secret: str) -> dict:
    try:
        # Supabase HS256 ile imzalar; audience 'authenticated'.
        return jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Geçersiz token: {exc}",
        ) from exc


async def current_user(
    authorization: str = Header(default=""),
    settings: Settings = Depends(get_settings),
) -> CurrentUser:
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization: Bearer <token> bekleniyor.",
        )
    token = authorization.split(" ", 1)[1].strip()
    payload = _decode_token(token, settings.supabase_jwt_secret)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token 'sub' içermiyor.")
    return CurrentUser(id=user_id, email=payload.get("email"))


async def require_premium(
    user: CurrentUser = Depends(current_user),
) -> CurrentUser:
    """Premium/elite tier gerektiren uçlar için (kahve/el falı)."""
    sb = get_supabase()
    tier = get_user_tier(sb, user.id)
    if tier not in ("premium", "elite"):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Bu özellik premium aboneliği gerektirir.",
        )
    return user
