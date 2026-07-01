"""OpenAI istemcisi — tüm AI çağrıları buradan ve HER ZAMAN safety katmanıyla.

Flutter'dan asla OpenAI çağrısı yapılmaz; key yalnızca backend'de.
"""
import base64
import json
from typing import Any

from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.services.ai.gemini_client import complete_json_gemini, complete_text_gemini
from app.services.ai.safety import SAFETY_SYSTEM_PROMPT

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=get_settings().openai_api_key)
    return _client


def _messages(system: str, user_content: Any) -> list[dict[str, Any]]:
    # Safety HER ZAMAN ilk sistem mesajı.
    return [
        {"role": "system", "content": SAFETY_SYSTEM_PROMPT},
        {"role": "system", "content": system},
        {"role": "user", "content": user_content},
    ]


@retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=4))
async def _openai_json(system: str, user_text: str) -> dict[str, Any]:
    s = get_settings()
    resp = await _get_client().chat.completions.create(
        model=s.openai_chat_model,
        messages=_messages(system, user_text),
        response_format={"type": "json_object"},
        temperature=0.8,
    )
    return json.loads(resp.choices[0].message.content or "{}")


async def complete_json(system: str, user_text: str) -> dict[str, Any]:
    """JSON modunda yorum üret. OpenAI çökerse (kota/limit) Gemini'ye düşer."""
    try:
        return await _openai_json(system, user_text)
    except Exception:
        return await complete_json_gemini(system, user_text)


@retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=4))
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
        temperature=0.8,
    )
    return resp.choices[0].message.content or ""


async def complete_chat(system: str, history: list[dict[str, str]], message: str) -> str:
    """Düz metin sohbet yanıtı. OpenAI çökerse Gemini'ye düşer."""
    try:
        return await _openai_chat(system, history, message)
    except Exception:
        return await complete_text_gemini(system, history, message)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
async def vision_extract_symbols(prompt: str, image_bytes: bytes) -> dict[str, Any]:
    """Fotoğraftan yalnızca sembol listesi çıkar (yorum değil). Foto saklanmaz."""
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
    )
    return json.loads(resp.choices[0].message.content or "{}")


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
async def embed(text: str) -> list[float]:
    """text-embedding-3-small ile 1536-boyut embedding."""
    s = get_settings()
    resp = await _get_client().embeddings.create(
        model=s.openai_embed_model, input=text
    )
    return resp.data[0].embedding
