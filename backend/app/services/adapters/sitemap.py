import httpx
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

from app.services.adapters.base import USER_AGENT, BaseAdapter, RawFinding, is_allowed_by_robots


class SitemapAdapter(BaseAdapter):
    """Parses an XML sitemap and filters URLs by a keyword list in config
    (e.g. config={"keywords": ["מכרז", "tender", "רכש"]}) - useful for large
    institutional sites without a dedicated tenders feed."""

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=20))
    async def fetch(self) -> list[RawFinding]:
        keywords = [k.lower() for k in self.config.get("keywords", ["מכרז", "רכש", "tender", "קול-קורא", "ספקים"])]
        async with httpx.AsyncClient(headers={"User-Agent": USER_AGENT}, follow_redirects=True) as client:
            if not await is_allowed_by_robots(self.source_url, client):
                raise PermissionError(f"robots.txt disallows crawling {self.source_url}")
            resp = await client.get(self.source_url, timeout=30)
            resp.raise_for_status()

        soup = BeautifulSoup(resp.content, "xml")
        findings: list[RawFinding] = []
        for loc in soup.find_all("loc"):
            url = loc.get_text(strip=True)
            if any(kw in url.lower() for kw in keywords):
                findings.append(RawFinding(title=url.rsplit("/", 1)[-1] or url, source_url=url))
        return findings
