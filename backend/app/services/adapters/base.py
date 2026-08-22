"""Adapter framework for the multi-source collection engine (spec section 2 & 21).

Every source in the `sources` table has a `source_type` (html/api/rss/sitemap/manual)
and a JSON `config_json`. An adapter turns one source into a list of RawFinding
objects; the crawl_source worker task then runs dedup + scoring + persistence on
each finding. Adding a new source type = adding one new adapter class + registering
it in ADAPTER_REGISTRY; no other code changes.

Legality/compliance (spec section 33): adapters must respect robots.txt, must not
bypass login/CAPTCHA/paywalls, and must back off on rate limits/errors rather than
retry aggressively forever.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser

import httpx

USER_AGENT = "EPLeadsBot/1.0 (+business intelligence crawler; respects robots.txt)"


@dataclass
class RawFinding:
    """One unprocessed opportunity/document found by a source scan."""

    title: str
    source_url: str
    record_type_hint: str = "tender"  # "tender" | "project"
    published_text: str | None = None
    raw_html: str | None = None
    raw_text: str | None = None
    pdf_url: str | None = None
    found_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    extra: dict = field(default_factory=dict)


class RobotsError(RuntimeError):
    pass


async def is_allowed_by_robots(url: str, client: httpx.AsyncClient) -> bool:
    from urllib.parse import urlparse

    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    try:
        resp = await client.get(robots_url, timeout=10)
        if resp.status_code >= 400:
            return True  # no robots.txt -> allowed by default
        rp = RobotFileParser()
        rp.parse(resp.text.splitlines())
        return rp.can_fetch(USER_AGENT, url)
    except httpx.HTTPError:
        return True  # fail-open on transient network errors, but log at call site


class BaseAdapter(ABC):
    def __init__(self, source_url: str, config: dict | None = None):
        self.source_url = source_url
        self.config = config or {}

    @abstractmethod
    async def fetch(self) -> list[RawFinding]:
        """Return newly-found or currently-listed items from this source."""
        raise NotImplementedError

    @staticmethod
    def resolve_url(base: str, href: str) -> str:
        return urljoin(base, href)
