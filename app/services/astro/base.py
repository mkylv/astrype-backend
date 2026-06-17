"""AstroProvider arayüzü — tüm astro hesaplamaları bunun arkasında soyutlanır."""
from abc import ABC, abstractmethod
from typing import Any

from app.models import BirthData


class AstroProvider(ABC):
    name: str

    @abstractmethod
    async def natal_chart(self, birth: BirthData) -> dict[str, Any]:
        """Gezegen pozisyonları, evler, açılar — ham JSON döner."""
        ...

    @abstractmethod
    async def daily_transits(self, birth: BirthData, date: str) -> dict[str, Any]:
        """Verilen tarih için transit/açı verisi."""
        ...

    @abstractmethod
    async def synastry(self, a: BirthData, b: BirthData) -> dict[str, Any]:
        """İki kişi arası sinastri ham verisi."""
        ...

    @abstractmethod
    async def natal_chart_svg(self, birth: BirthData, theme: str = "dark") -> bytes:
        """Natal chart görselini SVG bytes olarak döner."""
        ...
