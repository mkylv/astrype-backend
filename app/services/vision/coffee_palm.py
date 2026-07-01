"""Görsel fal — OpenAI vision ile sembol çıkarımı + ZORUNLU foto silme.

Gizlilik kararı (Bölüm 1): Yüklenen fotoğraf analiz sonrası HEMEN silinir.
Bu modül fotoğrafı yalnızca bellekte (bytes) tutar; diske/Storage'a yazmaz.
Çağıran taraf yalnızca sembol listesi + metin sonucu arşivler.
"""
from typing import Any

from app.services.ai import prompts
from app.services.ai.openai_client import vision_extract_symbols


async def extract_coffee_symbols(image_bytes: bytes) -> list[str]:
    """Kahve falı fotoğrafından sembol listesi. Foto saklanmaz."""
    data: dict[str, Any] = await vision_extract_symbols(
        prompts.VISION_COFFEE_EXTRACT, image_bytes
    )
    return [str(s) for s in data.get("symbols", [])]


async def extract_palm_lines(image_bytes: bytes) -> list[str]:
    """El falı fotoğrafından çizgi/sembol listesi. Foto saklanmaz."""
    data: dict[str, Any] = await vision_extract_symbols(
        prompts.VISION_PALM_EXTRACT, image_bytes
    )
    return [str(s) for s in data.get("lines", [])]


async def extract_face_features(image_bytes: bytes) -> list[str]:
    """Yüz fotoğrafından sima özellikleri listesi. Foto saklanmaz."""
    data: dict[str, Any] = await vision_extract_symbols(
        prompts.VISION_FACE_EXTRACT, image_bytes
    )
    return [str(s) for s in data.get("features", [])]
