from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.database import get_db
from app.models.tender import Tender

router = APIRouter(prefix="/tenders", tags=["tenders"], dependencies=[Depends(get_current_user)])


@router.get("")
async def list_tenders(
    is_open: bool | None = None,
    closing_before: date | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    stmt = select(Tender)
    if is_open is not None:
        stmt = stmt.where(Tender.is_open == is_open)
    if closing_before is not None:
        stmt = stmt.where(Tender.submission_deadline <= closing_before)
    stmt = stmt.order_by(Tender.submission_deadline.asc().nulls_last())
    result = await db.execute(stmt)
    return [
        {
            "id": str(t.id), "lead_id": str(t.lead_id) if t.lead_id else None, "title": t.title,
            "tender_number": t.tender_number, "publishing_body": t.publishing_body,
            "submission_deadline": t.submission_deadline.isoformat() if t.submission_deadline else None,
            "is_open": t.is_open, "estimated_value": float(t.estimated_value) if t.estimated_value else None,
            "source_url": t.source_url,
        }
        for t in result.scalars().all()
    ]
