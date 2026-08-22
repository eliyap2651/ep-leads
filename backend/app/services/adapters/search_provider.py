"""External web-search adapter (spec section 20) - pluggable so switching provider
is a config/env change, not a code change. Default: Serper.dev (Google results API).
"""

from abc import ABC, abstractmethod

import httpx

from app.config import get_settings
from app.services.adapters.base import RawFinding

settings = get_settings()


class SearchProviderUnavailableError(RuntimeError):
    pass


class BaseSearchProvider(ABC):
    @abstractmethod
    async def search(self, query: str, num_results: int = 20) -> list[RawFinding]:
        raise NotImplementedError


class SerperSearchProvider(BaseSearchProvider):
    ENDPOINT = "https://google.serper.dev/search"

    async def search(self, query: str, num_results: int = 20) -> list[RawFinding]:
        if not settings.SERPER_API_KEY:
            raise SearchProviderUnavailableError(
                "SERPER_API_KEY אינו מוגדר - הוסף אותו לקובץ .env כדי להפעיל חיפוש חיצוני"
            )
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                self.ENDPOINT,
                headers={"X-API-KEY": settings.SERPER_API_KEY, "Content-Type": "application/json"},
                json={"q": query, "num": num_results, "gl": "il", "hl": "iw"},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()

        findings: list[RawFinding] = []
        for item in data.get("organic", []):
            findings.append(
                RawFinding(
                    title=item.get("title", "(ללא כותרת)"),
                    source_url=item.get("link", ""),
                    raw_text=item.get("snippet"),
                )
            )
        return findings


class BingSearchProvider(BaseSearchProvider):
    ENDPOINT = "https://api.bing.microsoft.com/v7.0/search"

    async def search(self, query: str, num_results: int = 20) -> list[RawFinding]:
        if not settings.BING_API_KEY:
            raise SearchProviderUnavailableError("BING_API_KEY אינו מוגדר")
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                self.ENDPOINT,
                headers={"Ocp-Apim-Subscription-Key": settings.BING_API_KEY},
                params={"q": query, "count": num_results, "mkt": "he-IL"},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
        findings = []
        for item in data.get("webPages", {}).get("value", []):
            findings.append(
                RawFinding(title=item.get("name", ""), source_url=item.get("url", ""), raw_text=item.get("snippet"))
            )
        return findings


def get_search_provider() -> BaseSearchProvider:
    provider = settings.SEARCH_PROVIDER.lower()
    if provider == "serper":
        return SerperSearchProvider()
    if provider == "bing":
        return BingSearchProvider()
    raise SearchProviderUnavailableError(f"ספק חיפוש לא נתמך או לא מוגדר: {provider}")
