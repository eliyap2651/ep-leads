from app.models.enums import SourceType
from app.services.adapters.base import BaseAdapter
from app.services.adapters.html_generic import HTMLListingAdapter
from app.services.adapters.rss import RSSAdapter
from app.services.adapters.sitemap import SitemapAdapter

ADAPTER_REGISTRY: dict[SourceType, type[BaseAdapter]] = {
    SourceType.RSS: RSSAdapter,
    SourceType.SITEMAP: SitemapAdapter,
    SourceType.HTML: HTMLListingAdapter,
}


def get_adapter_for_source(source_type: SourceType, url: str, config: dict | None) -> BaseAdapter:
    adapter_cls = ADAPTER_REGISTRY.get(source_type)
    if not adapter_cls:
        raise ValueError(f"No adapter registered for source_type={source_type}")
    return adapter_cls(url, config)
