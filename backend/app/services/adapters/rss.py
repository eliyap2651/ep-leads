import feedparser
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.services.adapters.base import USER_AGENT, BaseAdapter, RawFinding, is_allowed_by_robots


class RSSAdapter(BaseAdapter):
    """Generic RSS/Atom feed adapter - works for any source that publishes a feed
    (news sites, some municipality "tenders" pages, procurement portals)."""

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=20))
    async def fetch(self) -> list[RawFinding]:
        async with httpx.AsyncClient(headers={"User-Agent": USER_AGENT}, follow_redirects=True) as client:
            if not await is_allowed_by_robots(self.source_url, client):
                raise PermissionError(f"robots.txt disallows crawling {self.source_url}")
            resp = await client.get(self.source_url, timeout=30)
            resp.raise_for_status()

        parsed = feedparser.parse(resp.content)
        findings: list[RawFinding] = []
        for entry in parsed.entries:
            findings.append(
                RawFinding(
                    title=entry.get("title", "").strip() or "(ללא כותרת)",
                    source_url=entry.get("link", self.source_url),
                    published_text=entry.get("published", None),
                    raw_text=entry.get("summary", None),
                    extra={"tags": [t.term for t in entry.get("tags", [])] if entry.get("tags") else []},
                )
            )
        return findings
