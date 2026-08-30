from dataclasses import dataclass
from time import monotonic

from src.services.scraper import XbotGoScraper


@dataclass
class CachedLive:
    url: str
    expires_at: float


class LiveService:
    def __init__(self, scraper: XbotGoScraper, cache_seconds: int) -> None:
        self.scraper = scraper
        self.cache_seconds = cache_seconds
        self._cache: CachedLive | None = None

    async def get_current_url(self) -> str | None:
        now = monotonic()
        if self._cache and self._cache.expires_at > now:
            return self._cache.url

        # Selenium is blocking; run it outside the async event loop.
        url = await self.scraper.find_url_async()
        if url:
            self._cache = CachedLive(
                url=url,
                expires_at=now + self.cache_seconds,
            )
        else:
            self._cache = None
        return url
