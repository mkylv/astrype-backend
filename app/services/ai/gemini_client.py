"""Google Gemini istemcisi — Ebced / ilm-i hurûf yorumu için.

Astrype'ın geri kalanı OpenAI kullanır; Ebced modülü özellikle Gemini'ye
gider (kullanıcı tercihi). REST API (generativelanguage) + httpx; ek bağımlılık
yok. JSON çıktı istenir (responseMimeType=application/json).
"""
import json
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.services.ai.safety import SAFETY_SYSTEM_PROMPT

_TIMEOUT = httpx.Timeout(60.0)
_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
async def complete_json_gemini(system_prompt: str, context: str) -> dict[str, Any]:
    """Gemini'ye sistem promptu + context gönderip JSON yanıt döner.

    Safety katmanı her zaman önce eklenir (OpenAI client'ı ile aynı kural).
    """
    s = get_settings()
    system = f"{SAFETY_SYSTEM_PROMPT}\n\n{system_prompt}"
    url = f"{_BASE}/{s.gemini_model}:generateContent?key={s.gemini_api_key}"
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
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        r = await client.post(url, json=payload)
        r.raise_for_status()
        data = r.json()

    try:
        parts = data["candidates"][0]["content"]["parts"]
        text = "".join(p.get("text", "") for p in parts)
    except (KeyError, IndexError) as exc:
        raise RuntimeError(f"Gemini yanıtı çözümlenemedi: {data}") from exc

    return _parse_json(text)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
async def vision_json_gemini(prompt: str, image_bytes: bytes) -> dict[str, Any]:
    """Görselden JSON çıkarım (OpenAI vision çökerse fallback).

    Foto yalnızca istek gövdesinde base64 olarak gider; saklanmaz.
    """
    import base64

    s = get_settings()
    system = f"{SAFETY_SYSTEM_PROMPT}\n\n{prompt}"
    url = f"{_BASE}/{s.gemini_model}:generateContent?key={s.gemini_api_key}"
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
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        r = await client.post(url, json=payload)
        r.raise_for_status()
        data = r.json()
    try:
        parts = data["candidates"][0]["content"]["parts"]
        text = "".join(p.get("text", "") for p in parts)
    except (KeyError, IndexError) as exc:
        raise RuntimeError(f"Gemini vision yanıtı çözümlenemedi: {data}") from exc
    return _parse_json(text)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
async def complete_text_gemini(
    system_prompt: str, history: list[dict[str, str]], message: str
) -> str:
    """Düz metin sohbet yanıtı (OpenAI çökerse chat fallback'i)."""
    s = get_settings()
    system = f"{SAFETY_SYSTEM_PROMPT}\n\n{system_prompt}"
    url = f"{_BASE}/{s.gemini_model}:generateContent?key={s.gemini_api_key}"
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
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        r = await client.post(url, json=payload)
        r.raise_for_status()
        data = r.json()
    try:
        parts = data["candidates"][0]["content"]["parts"]
        return "".join(p.get("text", "") for p in parts)
    except (KeyError, IndexError) as exc:
        raise RuntimeError(f"Gemini yanıtı çözümlenemedi: {data}") from exc


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
