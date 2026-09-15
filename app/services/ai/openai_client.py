"""OpenAI istemcisi — tüm AI çağrıları buradan ve HER ZAMAN safety katmanıyla.

Flutter'dan asla OpenAI çağrısı yapılmaz; key yalnızca backend'de.
"""
import base64
import json
from typing import Any

from openai import AsyncOpenAI

from app.config import get_settings
from app.services.ai.gemini_client import (
    complete_text_gemini,
    json_gemini_retrying,
    vision_json_gemini,
)
from app.services.ai.resilience import (
    http_timeout,
    retry_transient,
    run_with_budget,
    with_fallback,
)
from app.services.ai.safety import SAFETY_SYSTEM_PROMPT

_client: AsyncOpenAI | None = None

# Embedding kısa bir çağrıdır; hafıza yazımı/recall asla isteği uzun bekletmemeli.
_EMBED_READ_TIMEOUT = 20.0
_EMBED_BUDGET = 45.0


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        s = get_settings()
        _client = AsyncOpenAI(
            api_key=s.openai_api_key,
            # Varsayılan 600s + SDK içi 2 retry yerine: açık timeout, SDK retry
            # KAPALI — retry tek yerde (resilience.retry_transient).
            timeout=http_timeout(s.ai_timeout_seconds, s.ai_connect_timeout_seconds),
            max_retries=0,
        )
    return _client


def _timeout(read: float):
    return http_timeout(read, get_settings().ai_connect_timeout_seconds)


def _primary(fn, *, budget: float):
    """OpenAI fazı: geçici hatalarda sınırlı retry (deneme + süre tavanı)."""
    s = get_settings()
    window = max(budget - s.gemini_timeout_seconds, budget / 2)
    return lambda: retry_transient(fn, attempts=s.ai_max_attempts, max_delay=window)


def _messages(system: str, user_content: Any) -> list[dict[str, Any]]:
    # Safety HER ZAMAN ilk sistem mesajı.
    return [
        {"role": "system", "content": SAFETY_SYSTEM_PROMPT},
        {"role": "system", "content": system},
        {"role": "user", "content": user_content},
    ]


def _model_kwargs(model: str, temperature: float) -> dict[str, Any]:
    """Modele göre doğru parametreler.

    GPT-5 (gpt-5.6-luna dahil) reasoning modelleri: temperature GÖNDERME (yalnız
    default 1 kabul, aksi halde 400 → Gemini fallback) + `max_completion_tokens`
    ile bol tavan ver (reasoning token'ları uzun çıktıyı kesmesin). Diğer
    modeller (gpt-4o/gpt-4.1): temperature'ı ilet."""
    if model.startswith("gpt-5"):
        return {"max_completion_tokens": 16000}
    return {"temperature": temperature}


async def _openai_json(system: str, user_text: str) -> dict[str, Any]:
    s = get_settings()
    resp = await _get_client().chat.completions.create(
        model=s.openai_chat_model,
        messages=_messages(system, user_text),
        response_format={"type": "json_object"},
        timeout=_timeout(s.ai_long_timeout_seconds),
        **_model_kwargs(s.openai_chat_model, 0.8),
    )
    return json.loads(resp.choices[0].message.content or "{}")


async def complete_json(system: str, user_text: str) -> dict[str, Any]:
    """JSON modunda yorum üret. OpenAI çökerse (kota/limit) Gemini'ye düşer.

    Toplam (OpenAI + retry + Gemini) AI_LONG_REQUEST_BUDGET ile sınırlı; aşımda
    AITimeoutError, iki sağlayıcı da hata verirse AIUnavailableError.
    """
    s = get_settings()
    budget = s.ai_long_request_budget_seconds
    return await with_fallback(
        _primary(lambda: _openai_json(system, user_text), budget=budget),
        lambda: json_gemini_retrying(system, user_text),
        budget=budget,
        fallback_reserve=s.gemini_timeout_seconds,
        label="json",
    )


async def _openai_chat(system: str, history: list[dict[str, str]], message: str) -> str:
    s = get_settings()
    msgs = [
        {"role": "system", "content": SAFETY_SYSTEM_PROMPT},
        {"role": "system", "content": system},
        *history,
        {"role": "user", "content": message},
    ]
    resp = await _get_client().chat.completions.create(
        model=s.openai_chat_model,
        messages=msgs,
        timeout=_timeout(s.ai_timeout_seconds),
        **_model_kwargs(s.openai_chat_model, 0.8),
    )
    return resp.choices[0].message.content or ""


async def complete_chat(system: str, history: list[dict[str, str]], message: str) -> str:
    """Düz metin sohbet yanıtı. OpenAI çökerse Gemini'ye düşer (AI_REQUEST_BUDGET)."""
    s = get_settings()
    budget = s.ai_request_budget_seconds
    return await with_fallback(
        _primary(lambda: _openai_chat(system, history, message), budget=budget),
        lambda: complete_text_gemini(system, history, message),
        budget=budget,
        fallback_reserve=s.gemini_timeout_seconds,
        label="chat",
    )


async def vision_extract_symbols(prompt: str, image_bytes: bytes) -> dict[str, Any]:
    """Fotoğraftan yalnızca gözlem listesi çıkar (yorum değil). Foto saklanmaz.

    OpenAI vision çökerse (kota/limit) Gemini vision'a düşer (AI_REQUEST_BUDGET).
    """
    s = get_settings()
    budget = s.ai_request_budget_seconds
    return await with_fallback(
        _primary(lambda: _openai_vision(prompt, image_bytes), budget=budget),
        lambda: vision_json_gemini(prompt, image_bytes),
        budget=budget,
        fallback_reserve=s.gemini_timeout_seconds,
        label="vision",
    )


async def _openai_vision(prompt: str, image_bytes: bytes) -> dict[str, Any]:
    s = get_settings()
    b64 = base64.b64encode(image_bytes).decode()
    resp = await _get_client().chat.completions.create(
        model=s.openai_vision_model,
        messages=[
            {"role": "system", "content": SAFETY_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
                    },
                ],
            },
        ],
        response_format={"type": "json_object"},
        temperature=0.4,
        timeout=_timeout(s.ai_timeout_seconds),
    )
    return json.loads(resp.choices[0].message.content or "{}")


async def embed(text: str) -> list[float]:
    """text-embedding-3-small ile 1536-boyut embedding (kısa bütçe; çağıranlar
    hatayı yutar — hafıza hiçbir modülü çökertmez)."""
    s = get_settings()

    async def _once() -> list[float]:
        resp = await _get_client().embeddings.create(
            model=s.openai_embed_model, input=text, timeout=_timeout(_EMBED_READ_TIMEOUT)
        )
        return resp.data[0].embedding

    return await run_with_budget(
        lambda: retry_transient(_once, attempts=s.ai_max_attempts, max_delay=_EMBED_BUDGET),
        budget=_EMBED_BUDGET,
        label="embed",
    )
