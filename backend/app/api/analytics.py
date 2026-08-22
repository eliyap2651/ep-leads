from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.database import get_db
from app.models.contact import Contact
from app.models.enums import LeadTier, RecordType
from app.models.lead import Lead
from app.models.links import LeadContact
from app.models.tender import Tender
from app.models.user import User

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard")
async def dashboard(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> dict:
    today = datetime.now(timezone.utc).date()
    week_end = today + timedelta(days=7)

    total_leads = (await db.execute(select(func.count(Lead.id)))).scalar_one()
    new_today = (await db.execute(
        select(func.count(Lead.id)).where(func.date(Lead.created_at) == today)
    )).scalar_one()
    hot_leads = (await db.execute(select(func.count(Lead.id)).where(Lead.tier == LeadTier.HOT))).scalar_one()
    open_tenders = (await db.execute(
        select(func.count(Tender.id)).where(Tender.is_open == True)  # noqa: E712
    )).scalar_one()
    closing_week = (await db.execute(
        select(func.count(Tender.id)).where(
            Tender.is_open == True, Tender.submission_deadline.between(today, week_end)  # noqa: E712
        )
    )).scalar_one()
    new_projects = (await db.execute(
        select(func.count(Lead.id)).where(
            Lead.record_type == RecordType.PROJECT, func.date(Lead.created_at) == today
        )
    )).scalar_one()
    with_contact = (await db.execute(
        select(func.count(func.distinct(LeadContact.lead_id)))
    )).scalar_one()
    without_contact = max(total_leads - with_contact, 0)
    pipeline_value = (await db.execute(select(func.coalesce(func.sum(Lead.estimated_value), 0)))).scalar_one()

    return {
        "total_leads": total_leads,
        "new_today": new_today,
        "hot_leads": hot_leads,
        "open_tenders": open_tenders,
        "closing_this_week": closing_week,
        "new_projects_today": new_projects,
        "leads_with_contact": with_contact,
        "leads_without_contact": without_contact,
        "estimated_pipeline_value": float(pipeline_value),
    }


@router.get("/by-day")
async def leads_by_day(days: int = 30, db: AsyncSession = Depends(get_db)) -> list[dict]:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    stmt = (
        select(func.date(Lead.created_at).label("day"), func.count(Lead.id))
        .where(Lead.created_at >= since)
        .group_by("day")
        .order_by("day")
    )
    result = await db.execute(stmt)
    return [{"day": str(day), "count": count} for day, count in result.all()]


@router.get("/by-domain")
async def leads_by_domain(db: AsyncSession = Depends(get_db)) -> list[dict]:
    stmt = select(Lead.domain, func.count(Lead.id)).group_by(Lead.domain)
    result = await db.execute(stmt)
    return [{"domain": d.value if d else "לא ידוע", "count": c} for d, c in result.all()]


@router.get("/by-region")
async def leads_by_region(db: AsyncSession = Depends(get_db)) -> list[dict]:
    stmt = select(Lead.region, func.count(Lead.id)).group_by(Lead.region)
    result = await db.execute(stmt)
    return [{"region": r.value, "count": c} for r, c in result.all()]


@router.get("/by-score")
async def leads_by_score(db: AsyncSession = Depends(get_db)) -> list[dict]:
    stmt = select(Lead.tier, func.count(Lead.id)).group_by(Lead.tier)
    result = await db.execute(stmt)
    return [{"tier": t.value, "count": c} for t, c in result.all()]


@router.get("/by-status")
async def leads_by_status(db: AsyncSession = Depends(get_db)) -> list[dict]:
    stmt = select(Lead.status, func.count(Lead.id)).group_by(Lead.status)
    result = await db.execute(stmt)
    return [{"status": s.value, "count": c} for s, c in result.all()]


@router.get("/tenders-closing")
async def tenders_closing(db: AsyncSession = Depends(get_db)) -> dict:
    today = datetime.now(timezone.utc).date()
    windows = {"today": 0, "tomorrow": 1, "3_days": 3, "7_days": 7, "30_days": 30}
    output: dict[str, int] = {}
    for label, offset in windows.items():
        target = today + timedelta(days=offset)
        count = (await db.execute(
            select(func.count(Tender.id)).where(
                Tender.is_open == True, Tender.submission_deadline == target  # noqa: E712
            )
        )).scalar_one()
        output[label] = count
    return output


@router.get("/top-opportunities")
async def top_opportunities(limit: int = 10, db: AsyncSession = Depends(get_db)) -> list[dict]:
    stmt = select(Lead).order_by(Lead.score.desc(), Lead.created_at.desc()).limit(limit)
    result = await db.execute(stmt)
    leads = result.scalars().all()
    return [
        {
            "id": str(lead.id),
            "title": lead.title,
            "score": lead.score,
            "tier": lead.tier.value,
            "estimated_value": float(lead.estimated_value) if lead.estimated_value else None,
            "deadline": lead.deadline.isoformat() if lead.deadline else None,
            "ai_summary": lead.ai_summary,
        }
        for lead in leads
    ]


@router.get("/daily-brief")
async def daily_brief(db: AsyncSession = Depends(get_db)) -> dict:
    """Spec section 48 - AI Daily Brief content (numbers computed deterministically;
    only the narrative wording is templated, not AI-generated, to avoid inventing figures)."""
    today = datetime.now(timezone.utc).date()
    week_end = today + timedelta(days=7)

    new_today = (await db.execute(
        select(func.count(Lead.id)).where(func.date(Lead.created_at) == today)
    )).scalar_one()
    hot_today = (await db.execute(
        select(func.count(Lead.id)).where(Lead.tier == LeadTier.HOT, func.date(Lead.created_at) == today)
    )).scalar_one()
    closing_week = (await db.execute(
        select(func.count(Tender.id)).where(
            Tender.is_open == True, Tender.submission_deadline.between(today, week_end)  # noqa: E712
        )
    )).scalar_one()
    new_projects = (await db.execute(
        select(func.count(Lead.id)).where(
            Lead.record_type == RecordType.PROJECT, func.date(Lead.created_at) == today
        )
    )).scalar_one()
    over_100k = (await db.execute(
        select(func.count(Lead.id)).where(Lead.estimated_value >= 100_000)
    )).scalar_one()

    top = await top_opportunities(limit=10, db=db)

    return {
        "date": today.isoformat(),
        "new_leads_found": new_today,
        "hot_leads": hot_today,
        "tenders_closing_7_days": closing_week,
        "new_projects": new_projects,
        "leads_over_100k": over_100k,
        "top_opportunities": top,
    }
