import httpx
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

from app.services.adapters.base import USER_AGENT, BaseAdapter, RawFinding, is_allowed_by_robots


class HTMLListingAdapter(BaseAdapter):
    """Generic listing-page scraper for "מכרזים" / "רכש" / "קולות קוראים" pages that
    have no feed/API. config supports an optional CSS selector for links:
    {"link_selector": "a.tender-link"} - default falls back to scanning all <a> tags
    whose text or href looks tender/procurement-related, which works reasonably for
    many Israeli municipal/institutional "tenders" pages without per-site tuning.
    """

    DEFAULT_KEYWORDS = ["מכרז", "רכש", "קול קורא", "הזמנה להציע הצעות", "מאגר ספקים", "tender", "rfp", "rfq"]

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=20))
    async def fetch(self) -> list[RawFinding]:
        selector = self.config.get("link_selector")
        keywords = [k.lower() for k in self.config.get("keywords", self.DEFAULT_KEYWORDS)]

        async with httpx.AsyncClient(headers={"User-Agent": USER_AGENT}, follow_redirects=True) as client:
            if not await is_allowed_by_robots(self.source_url, client):
                raise PermissionError(f"robots.txt disallows crawling {self.source_url}")
            resp = await client.get(self.source_url, timeout=30)
            resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "lxml")
        anchors = soup.select(selector) if selector else soup.find_all("a", href=True)

        findings: list[RawFinding] = []
        seen_urls: set[str] = set()
        for a in anchors:
            href = a.get("href")
            if not href:
                continue
            text = a.get_text(strip=True)
            haystack = f"{text} {href}".lower()
            if not selector and not any(kw in haystack for kw in keywords):
                continue
            full_url = self.resolve_url(self.source_url, href)
            if full_url in seen_urls:
                continue
            seen_urls.add(full_url)
            findings.append(
                RawFinding(
                    title=text or full_url,
                    source_url=full_url,
                    pdf_url=full_url if full_url.lower().endswith(".pdf") else None,
                )
            )
        return findings
