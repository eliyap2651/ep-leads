from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.deps import require_admin
from app.database import get_db
from app.models.enums import ScanRunStatus
from app.models.scan_run import ScanRun
from app.models.source import Source

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])
settings = get_settings()


@router.get("/health")
async def system_health(db: AsyncSession = Depends(get_db)) -> dict:
    db_ok = True
    try:
        await db.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001
        db_ok = False

    total_sources = (await db.execute(select(func.count(Source.id)))).scalar_one()
    active_sources = (await db.execute(select(func.count(Source.id)).where(Source.is_active == True))).scalar_one()  # noqa: E712
    error_sources = (await db.execute(select(func.count(Source.id)).where(Source.status == "error"))).scalar_one()

    last_scan = (await db.execute(select(func.max(ScanRun.finished_at)))).scalar_one()
    failed_jobs = (await db.execute(
        select(func.count(ScanRun.id)).where(ScanRun.status == ScanRunStatus.FAILED)
    )).scalar_one()
    successful_jobs = (await db.execute(
        select(func.count(ScanRun.id)).where(ScanRun.status == ScanRunStatus.SUCCESS)
    )).scalar_one()

    return {
        "database": "ok" if db_ok else "error",
        "ai_configured": bool(settings.ANTHROPIC_API_KEY),
        "search_configured": bool(settings.SERPER_API_KEY or settings.BING_API_KEY),
        "email_configured": bool(settings.SMTP_HOST),
        "sources_total": total_sources,
        "sources_active": active_sources,
        "sources_with_errors": error_sources,
        "last_scan_at": last_scan.isoformat() if last_scan else None,
        "failed_jobs": failed_jobs,
        "successful_jobs": successful_jobs,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/scan-runs")
async def recent_scan_runs(limit: int = 50, db: AsyncSession = Depends(get_db)) -> list[dict]:
    result = await db.execute(select(ScanRun).order_by(ScanRun.created_at.desc()).limit(limit))
    return [
        {
            "id": str(r.id),
            "source_id": str(r.source_id) if r.source_id else None,
            "task_name": r.task_name,
            "status": r.status.value,
            "items_found": r.items_found,
            "new_leads": r.new_leads,
            "error": r.error,
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "finished_at": r.finished_at.isoformat() if r.finished_at else None,
        }
        for r in result.scalars().all()
    ]
