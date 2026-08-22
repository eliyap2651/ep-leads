import io

import pandas as pd
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.database import get_db
from app.models.enums import Domain, LeadTier, Region
from app.models.lead import Lead

router = APIRouter(prefix="/export", tags=["export"])


async def _filtered_leads(db: AsyncSession, domain, region, tier, min_score) -> list[Lead]:
    stmt = select(Lead)
    if domain:
        stmt = stmt.where(Lead.domain == domain)
    if region:
        stmt = stmt.where(Lead.region == region)
    if tier:
        stmt = stmt.where(Lead.tier == tier)
    if min_score is not None:
        stmt = stmt.where(Lead.score >= min_score)
    result = await db.execute(stmt.order_by(Lead.score.desc()))
    return list(result.scalars().all())


def _to_dataframe(leads: list[Lead]) -> pd.DataFrame:
    rows = [
        {
            "כותרת": lead.title,
            "סוג": lead.record_type.value,
            "תחום": lead.domain.value if lead.domain else "",
            "עיר": lead.city or "",
            "אזור": lead.region.value,
            "שווי משוער": float(lead.estimated_value) if lead.estimated_value else "",
            "מועד אחרון": lead.deadline.isoformat() if lead.deadline else "",
            "ציון": lead.score,
            "דירוג": lead.tier.value,
            "סטטוס": lead.status.value,
            "נוצר": lead.created_at.isoformat(),
        }
        for lead in leads
    ]
    return pd.DataFrame(rows)


@router.get("/leads.csv")
async def export_csv(
    domain: Domain | None = None,
    region: Region | None = None,
    tier: LeadTier | None = None,
    min_score: int | None = None,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    leads = await _filtered_leads(db, domain, region, tier, min_score)
    df = _to_dataframe(leads)
    buffer = io.StringIO()
    df.to_csv(buffer, index=False, encoding="utf-8-sig")
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=leads.csv"},
    )


@router.get("/leads.xlsx")
async def export_excel(
    domain: Domain | None = None,
    region: Region | None = None,
    tier: LeadTier | None = None,
    min_score: int | None = None,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    leads = await _filtered_leads(db, domain, region, tier, min_score)
    df = _to_dataframe(leads)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Leads")
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=leads.xlsx"},
    )
