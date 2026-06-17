"""Auth bağımlılığı — Supabase JWT doğrular, current_user döner.

Supabase yeni projeler token'ları ASİMETRİK (ES256/RS256) imzalar; doğrulama
projenin JWKS public anahtarlarıyla yapılır. Eski HS256 (paylaşılan secret)
token'ları da desteklenir (geriye dönük uyum).
"""
import time
from dataclasses import dataclass

import httpx
from fastapi import Depends, Header, HTTPException, status
from jose import JWTError, jwt

from app.config import Settings, get_settings
from app.db.supabase_client import get_supabase, get_user_tier

# JWKS önbelleği (kid -> key). 1 saat TTL.
_JWKS: dict[str, object] = {"keys": None, "ts": 0.0}
_JWKS_TTL = 3600.0


@dataclass
class CurrentUser:
    id: str
    email: str | None = None


async def _fetch_jwks(settings: Settings, force: bool = False) -> list[dict]:
    now = time.time()
    if not force and _JWKS["keys"] and now - _JWKS["ts"] < _JWKS_TTL:
        return _JWKS["keys"]  # type: ignore[return-value]
    url = f"{settings.supabase_url}/auth/v1/.well-known/jwks.json"
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(url)
        r.raise_for_status()
        keys = r.json().get("keys", [])
    _JWKS["keys"] = keys
    _JWKS["ts"] = now
    return keys


async def _decode(token: str, settings: Settings) -> dict:
    try:
        header = jwt.get_unverified_header(token)
    except JWTError as exc:
        raise HTTPException(status_code=401, detail=f"Geçersiz token: {exc}") from exc

    alg = header.get("alg")
    opts = {"audience": "authenticated"}

    try:
        if alg == "HS256":
            return jwt.decode(
                token, settings.supabase_jwt_secret, algorithms=["HS256"], **opts
            )
        # Asimetrik: JWKS'ten kid ile eşleşen public anahtar.
        kid = header.get("kid")
        keys = await _fetch_jwks(settings)
        jwk = next((k for k in keys if k.get("kid") == kid), None)
        if jwk is None:
            # Anahtar rotasyonu olmuş olabilir; önbelleği zorla yenile.
            keys = await _fetch_jwks(settings, force=True)
            jwk = next((k for k in keys if k.get("kid") == kid), None)
        if jwk is None:
            raise HTTPException(status_code=401, detail="İmza anahtarı bulunamadı.")
        return jwt.decode(token, jwk, algorithms=[alg], **opts)
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
    payload = await _decode(token, settings)
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
