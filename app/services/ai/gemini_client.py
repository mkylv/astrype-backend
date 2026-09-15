"""Google Gemini istemcisi — Ebced / ilm-i hurûf yorumu için.

Astrype'ın geri kalanı OpenAI kullanır; Ebced modülü özellikle Gemini'ye
gider (kullanıcı tercihi). REST API (generativelanguage) + httpx; ek bağımlılık
yok. JSON çıktı istenir (responseMimeType=application/json).
"""
import json
from typing import Any

import httpx

from app.config import get_settings
from app.services.ai.resilience import (
    ProviderHTTPError,
    http_timeout,
    retry_transient,
    run_with_budget,
)
from app.services.ai.safety import SAFETY_SYSTEM_PROMPT

_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


async def _generate(payload: dict[str, Any]) -> dict[str, Any]:
    """generateContent POST. Key URL'de DEĞİL `x-goog-api-key` header'ında;
    hata mesajları URL/key içermez (log'a sızmasın)."""
    s = get_settings()
    url = f"{_BASE}/{s.gemini_model}:generateContent"
    headers = {"x-goog-api-key": s.gemini_api_key}
    timeout = http_timeout(s.gemini_timeout_seconds, s.ai_connect_timeout_seconds)
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(url, json=payload, headers=headers)
    if r.status_code >= 400:
        raise ProviderHTTPError("Gemini", r.status_code)
    return r.json()


def _retrying(fn):
    s = get_settings()
    return retry_transient(
        fn, attempts=s.ai_max_attempts, max_delay=s.gemini_timeout_seconds
    )


async def complete_json_gemini(system_prompt: str, context: str) -> dict[str, Any]:
    """Doğrudan Gemini JSON yorumu (Ebced) — toplam bütçeyle sınırlı.

    Bütçe aşımı/hata → AITimeoutError/AIUnavailableError (main.py 504/503).
    """
    s = get_settings()
    return await run_with_budget(
        lambda: json_gemini_retrying(system_prompt, context),
        budget=s.ai_long_request_budget_seconds,
        label="gemini-json",
    )


async def json_gemini_retrying(system_prompt: str, context: str) -> dict[str, Any]:
    """OpenAI fallback'i için: geçici hatalarda sınırlı retry, bütçe dışarıda."""
    return await _retrying(lambda: _json_once(system_prompt, context))


async def vision_json_gemini(prompt: str, image_bytes: bytes) -> dict[str, Any]:
    return await _retrying(lambda: _vision_once(prompt, image_bytes))


async def complete_text_gemini(
    system_prompt: str, history: list[dict[str, str]], message: str
) -> str:
    return await _retrying(lambda: _text_once(system_prompt, history, message))


async def _json_once(system_prompt: str, context: str) -> dict[str, Any]:
    """Gemini'ye sistem promptu + context gönderip JSON yanıt döner.

    Safety katmanı her zaman önce eklenir (OpenAI client'ı ile aynı kural).
    """
    system = f"{SAFETY_SYSTEM_PROMPT}\n\n{system_prompt}"
    payload = {
        "system_instruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": context}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.95,
            "maxOutputTokens": 8192,
            # 2.5 thinking modelinde JSON'un kesilmemesi için düşünmeyi kapat.
            "thinkingConfig": {"thinkingBudget": 0},
        },
    }
    data = await _generate(payload)

    try:
        parts = data["candidates"][0]["content"]["parts"]
        text = "".join(p.get("text", "") for p in parts)
    except (KeyError, IndexError) as exc:
        raise RuntimeError("Gemini yanıtı çözümlenemedi") from exc

    return _parse_json(text)


async def _vision_once(prompt: str, image_bytes: bytes) -> dict[str, Any]:
    """Görselden JSON çıkarım (OpenAI vision çökerse fallback).

    Foto yalnızca istek gövdesinde base64 olarak gider; saklanmaz.
    """
    import base64

    system = f"{SAFETY_SYSTEM_PROMPT}\n\n{prompt}"
    payload = {
        "system_instruction": {"parts": [{"text": system}]},
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": base64.b64encode(image_bytes).decode(),
                        }
                    },
                ],
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.4,
            "maxOutputTokens": 2048,
            "thinkingConfig": {"thinkingBudget": 0},
        },
    }
    data = await _generate(payload)
    try:
        parts = data["candidates"][0]["content"]["parts"]
        text = "".join(p.get("text", "") for p in parts)
    except (KeyError, IndexError) as exc:
        raise RuntimeError("Gemini vision yanıtı çözümlenemedi") from exc
    return _parse_json(text)


async def _text_once(
    system_prompt: str, history: list[dict[str, str]], message: str
) -> str:
    """Düz metin sohbet yanıtı (OpenAI çökerse chat fallback'i)."""
    system = f"{SAFETY_SYSTEM_PROMPT}\n\n{system_prompt}"
    contents = [
        {
            "role": "model" if m.get("role") == "assistant" else "user",
            "parts": [{"text": m.get("content", "")}],
        }
        for m in history
    ]
    contents.append({"role": "user", "parts": [{"text": message}]})
    payload = {
        "system_instruction": {"parts": [{"text": system}]},
        "contents": contents,
        "generationConfig": {
            "temperature": 0.85,
            "maxOutputTokens": 2048,
            "thinkingConfig": {"thinkingBudget": 0},
        },
    }
    data = await _generate(payload)
    try:
        parts = data["candidates"][0]["content"]["parts"]
        return "".join(p.get("text", "") for p in parts)
    except (KeyError, IndexError) as exc:
        raise RuntimeError("Gemini yanıtı çözümlenemedi") from exc


def _parse_json(text: str) -> dict[str, Any]:
    """JSON'u çöz; markdown fence / önek-sonek varsa ayıkla."""
    t = text.strip()
    if t.startswith("```"):
        t = t.split("```", 2)[1]
        if t.startswith("json"):
            t = t[4:]
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        start, end = t.find("{"), t.rfind("}")
        if start != -1 and end != -1:
            return json.loads(t[start : end + 1])
        raise
