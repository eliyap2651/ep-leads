from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_manager_or_admin
from app.database import get_db
from app.models.search_query import SearchQuery
from app.models.source import Source
from app.services.adapters import get_adapter_for_source
from app.services.adapters.search_provider import SearchProviderUnavailableError, get_search_provider
from app.services.ingestion import ingest_finding

router = APIRouter(prefix="/search", tags=["search"], dependencies=[Depends(require_manager_or_admin)])


@router.post("/run")
async def run_search_now(db: AsyncSession = Depends(get_db)) -> dict:
    """Manually trigger one round of: all active search queries via the external
    search provider + all active sources via their adapters. Same code path the
    scheduled Celery beat job uses (see app/workers/tasks.py)."""
    created, updated, errors = 0, 0, []

    queries_result = await db.execute(select(SearchQuery).where(SearchQuery.is_active == True))  # noqa: E712
    try:
        provider = get_search_provider()
        for query in queries_result.scalars().all():
            findings = await provider.search(query.text)
            for finding in findings:
                _, is_new = await ingest_finding(db, finding, source_name=f"חיפוש: {query.text}")
                created += 1 if is_new else 0
                updated += 0 if is_new else 1
    except SearchProviderUnavailableError as exc:
        errors.append(str(exc))

    sources_result = await db.execute(select(Source).where(Source.is_active == True))  # noqa: E712
    for source in sources_result.scalars().all():
        try:
            adapter = get_adapter_for_source(source.source_type, source.url, None)
            findings = await adapter.fetch()
            for finding in findings:
                _, is_new = await ingest_finding(db, finding, source_id=source.id, source_name=source.name)
                created += 1 if is_new else 0
                updated += 0 if is_new else 1
            source.status = "ok"
            source.result_count = len(findings)
        except Exception as exc:  # noqa: BLE001 - one source failing must not stop the others
            source.status = "error"
            source.last_error = str(exc)
            errors.append(f"{source.name}: {exc}")

    await db.commit()
    return {"new_leads": created, "updated_leads": updated, "errors": errors}
