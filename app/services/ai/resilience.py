"""AI çağrıları için zaman aşımı / retry / fallback bütçesi.

Kurallar:
- Retry yalnızca GEÇİCİ hatalarda (timeout, bağlantı, 429, 5xx). 4xx (geçersiz
  istek, auth, kota bitti) asla tekrar denenmez.
- Her retry döngüsü hem deneme sayısıyla hem toplam süreyle sınırlıdır.
- Birincil (OpenAI) + fallback (Gemini) zinciri tek bir toplam bütçeye bağlıdır;
  bütçe aşılırsa `AITimeoutError`, sağlayıcılar hata verirse `AIUnavailableError`.
  main.py bunları 504/503'e çevirir (sızıntısız kısa mesaj).
- İstek başına mutlak son tarih (`request_deadline`) ContextVar'da tutulur;
  bir HTTP isteğindeki birden çok AI çağrısı bu tavanı birlikte paylaşır.
"""
from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from contextlib import contextmanager
from contextvars import ContextVar
from typing import TypeVar

import httpx
import openai
from tenacity import (
    AsyncRetrying,
    retry_if_exception,
    stop_after_attempt,
    stop_after_delay,
    wait_exponential,
)

T = TypeVar("T")

log = logging.getLogger("astrype.ai")

# Monotonic mutlak son tarih (time.monotonic() tabanı) ya da None (sınırsız).
_deadline: ContextVar[float | None] = ContextVar("astrype_ai_deadline", default=None)


class AIUnavailableError(Exception):
    """AI sağlayıcıları yanıt veremedi (kullanıcıya 503)."""

    status_code = 503
    code = "AI_UNAVAILABLE"
    public_message = "Yorum şu an hazırlanamadı. Lütfen biraz sonra tekrar dene."


class AITimeoutError(AIUnavailableError):
    """AI üretimi zaman bütçesini aştı (kullanıcıya 504)."""

    status_code = 504
    code = "AI_TIMEOUT"
    public_message = "Yorum beklenenden uzun sürdü. Lütfen biraz sonra tekrar dene."


# ---------------------------------------------------------------- deadline


@contextmanager
def request_deadline(seconds: float):
    """Bu blok içindeki tüm AI çağrılarına mutlak toplam tavan koy."""
    new = time.monotonic() + seconds
    current = _deadline.get()
    token = _deadline.set(new if current is None else min(current, new))
    try:
        yield
    finally:
        _deadline.reset(token)


def effective_budget(budget: float) -> float:
    """Çağrının kendi bütçesi ile istek son tarihine kalan sürenin küçüğü."""
    dl = _deadline.get()
    if dl is None:
        return budget
    return min(budget, dl - time.monotonic())


# ---------------------------------------------------------------- transient


def is_transient(exc: BaseException) -> bool:
    """Tekrar denemeye değer geçici hata mı? (timeout / bağlantı / 429 / 5xx)"""
    if isinstance(exc, (asyncio.TimeoutError, TimeoutError)):
        return True
    # OpenAI SDK
    if isinstance(exc, (openai.APITimeoutError, openai.APIConnectionError)):
        return True
    if isinstance(exc, openai.RateLimitError):
        # Kota bitti (insufficient_quota) kalıcıdır; beklemek çözmez.
        return getattr(exc, "code", None) != "insufficient_quota"
    if isinstance(exc, openai.APIStatusError):
        return exc.status_code >= 500
    # httpx (Gemini)
    if isinstance(exc, (httpx.TimeoutException, httpx.TransportError)):
        return True
    if isinstance(exc, ProviderHTTPError):
        return exc.status_code == 429 or exc.status_code >= 500
    return False


class ProviderHTTPError(Exception):
    """URL/key içermeyen sağlayıcı HTTP hatası."""

    def __init__(self, provider: str, status_code: int):
        super().__init__(f"{provider} HTTP {status_code}")
        self.status_code = status_code


def describe(exc: BaseException) -> str:
    """Log için sızıntısız kısa açıklama (mesaj gövdesi/URL yok)."""
    status = getattr(exc, "status_code", None)
    return f"{type(exc).__name__}" + (f"({status})" if status else "")


# ---------------------------------------------------------------- retry


async def retry_transient(
    fn: Callable[[], Awaitable[T]], *, attempts: int, max_delay: float
) -> T:
    """`fn`'i yalnızca geçici hatalarda, deneme + süre tavanıyla tekrar dene."""
    async for attempt in AsyncRetrying(
        stop=stop_after_attempt(max(1, attempts)) | stop_after_delay(max_delay),
        wait=wait_exponential(min=1, max=4),
        retry=retry_if_exception(is_transient),
        reraise=True,
    ):
        with attempt:
            return await fn()
    raise AssertionError("unreachable")  # pragma: no cover


# ---------------------------------------------------------------- budget


async def run_with_budget(
    fn: Callable[[], Awaitable[T]], *, budget: float, label: str
) -> T:
    """Tek zincirli (fallback'siz) çağrı: toplam bütçe + temiz hata sınıfı."""
    total = effective_budget(budget)
    if total <= 0:
        raise AITimeoutError()
    try:
        return await asyncio.wait_for(fn(), total)
    except (asyncio.TimeoutError, TimeoutError):
        log.warning("AI %s: bütçe aşıldı (%.0fs)", label, total)
        raise AITimeoutError() from None
    except AIUnavailableError:
        raise
    except Exception as exc:
        log.warning("AI %s başarısız: %s", label, describe(exc))
        raise AIUnavailableError() from None


async def with_fallback(
    primary: Callable[[], Awaitable[T]],
    fallback: Callable[[], Awaitable[T]],
    *,
    budget: float,
    fallback_reserve: float,
    label: str,
) -> T:
    """Birincil → (hata/timeout) → fallback; hepsi tek `budget` içinde.

    Birincil faz, fallback'e `fallback_reserve` kadar süre kalacak şekilde
    kesilir. Başarılı yolda davranış aynen korunur.
    """
    total = effective_budget(budget)
    if total <= 0:
        raise AITimeoutError()
    start = time.monotonic()
    primary_window = total - fallback_reserve
    if primary_window < total / 2:
        primary_window = total / 2  # yanlış yapılandırmada birincile en az yarısı

    primary_timed_out = False
    try:
        return await asyncio.wait_for(primary(), primary_window)
    except (asyncio.TimeoutError, TimeoutError):
        primary_timed_out = True
        log.warning("AI %s: birincil zaman aşımı (%.0fs) → fallback", label, primary_window)
    except Exception as exc:
        log.warning("AI %s: birincil başarısız %s → fallback", label, describe(exc))

    remaining = total - (time.monotonic() - start)
    if remaining <= 0:
        raise AITimeoutError()
    try:
        return await asyncio.wait_for(fallback(), remaining)
    except (asyncio.TimeoutError, TimeoutError):
        log.warning("AI %s: fallback zaman aşımı (%.0fs)", label, remaining)
        raise AITimeoutError() from None
    except Exception as exc:
        log.warning("AI %s: fallback başarısız %s", label, describe(exc))
        if primary_timed_out or is_timeout(exc):
            raise AITimeoutError() from None
        raise AIUnavailableError() from None


def is_timeout(exc: BaseException) -> bool:
    return isinstance(
        exc,
        (asyncio.TimeoutError, TimeoutError, openai.APITimeoutError, httpx.TimeoutException),
    )


def http_timeout(read: float, connect: float) -> httpx.Timeout:
    return httpx.Timeout(read, connect=connect)


__all__ = [
    "AIUnavailableError",
    "AITimeoutError",
    "ProviderHTTPError",
    "effective_budget",
    "http_timeout",
    "is_transient",
    "request_deadline",
    "retry_transient",
    "run_with_budget",
    "with_fallback",
]
