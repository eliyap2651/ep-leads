import json
import uuid
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user, require_manager_or_admin
from app.database import get_db
from app.models.activity import Activity, FollowUpTask, Note
from app.models.contact import Contact
from app.models.enums import Domain, LeadStatus, LeadTier, RecordType, Region, UserRole
from app.models.lead import Lead
from app.models.links import LeadContact
from app.models.user import User
from app.schemas.lead import (
    ActivityCreate,
    ActivityOut,
    LeadDetail,
    LeadListItem,
    LeadUpdate,
    NoteCreate,
    NoteOut,
)
from app.services.ai_engine import AIEngine, AIUnavailableError

router = APIRouter(prefix="/leads", tags=["leads"])


def _lead_to_list_item(lead: Lead, has_contact: bool, has_phone: bool) -> LeadListItem:
    item = LeadListItem.model_validate(lead)
    item.has_contact = has_contact
    item.has_phone = has_phone
    return item


@router.get("", response_model=list[LeadListItem])
async def list_leads(
    q: str | None = Query(None, description="חיפוש חופשי בכותרת/עיר"),
    domain: Domain | None = None,
    region: Region | None = None,
    record_type: RecordType | None = None,
    status_filter: LeadStatus | None = Query(None, alias="status"),
    tier: LeadTier | None = None,
    min_score: int | None = None,
    max_score: int | None = None,
    min_value: float | None = None,
    has_contact: bool | None = None,
    deadline_before: date | None = None,
    assigned_to_id: uuid.UUID | None = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[LeadListItem]:
    stmt = select(Lead).options(selectinload(Lead.lead_contacts).selectinload(LeadContact.contact))

    if current_user.role == UserRole.SALES_AGENT:
        stmt = stmt.where(Lead.assigned_to_id == current_user.id)

    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Lead.title.ilike(like), Lead.city.ilike(like)))
    if domain:
        stmt = stmt.where(Lead.domain == domain)
    if region:
        stmt = stmt.where(Lead.region == region)
    if record_type:
        stmt = stmt.where(Lead.record_type == record_type)
    if status_filter:
        stmt = stmt.where(Lead.status == status_filter)
    if tier:
        stmt = stmt.where(Lead.tier == tier)
    if min_score is not None:
        stmt = stmt.where(Lead.score >= min_score)
    if max_score is not None:
        stmt = stmt.where(Lead.score <= max_score)
    if min_value is not None:
        stmt = stmt.where(Lead.estimated_value >= min_value)
    if deadline_before is not None:
        stmt = stmt.where(Lead.deadline <= deadline_before)
    if assigned_to_id is not None:
        stmt = stmt.where(Lead.assigned_to_id == assigned_to_id)

    stmt = stmt.order_by(Lead.score.desc(), Lead.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    leads = result.scalars().unique().all()

    items = []
    for lead in leads:
        contacts = [lc.contact for lc in lead.lead_contacts if lc.contact]
        hc = len(contacts) > 0
        hp = any(c.phone for c in contacts)
        if has_contact is not None and hc != has_contact:
            continue
        items.append(_lead_to_list_item(lead, hc, hp))
    return items


@router.get("/{lead_id}", response_model=LeadDetail)
async def get_lead(
    lead_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Lead:
    result = await db.execute(
        select(Lead)
        .options(selectinload(Lead.lead_contacts).selectinload(LeadContact.contact))
        .where(Lead.id == lead_id)
    )
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="ליד לא נמצא")
    if current_user.role == UserRole.SALES_AGENT and lead.assigned_to_id != current_user.id:
        raise HTTPException(status_code=403, detail="אין הרשאה לצפות בליד זה")
    contacts = [lc.contact for lc in lead.lead_contacts if lc.contact]
    detail = LeadDetail.model_validate(lead)
    detail.has_contact = len(contacts) > 0
    detail.has_phone = any(c.phone for c in contacts)
    return detail


@router.patch("/{lead_id}", response_model=LeadDetail)
async def update_lead(
    lead_id: uuid.UUID,
    payload: LeadUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Lead:
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="ליד לא נמצא")

    old_status = lead.status
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(lead, field, value)
    await db.flush()

    if payload.status and payload.status != old_status:
        db.add(
            Activity(
                lead_id=lead.id,
                user_id=current_user.id,
                activity_type="status_change",
                description=f"סטטוס שונה מ-{old_status.value} ל-{payload.status.value}",
            )
        )
    await db.commit()
    await db.refresh(lead)
    return lead


@router.delete("/{lead_id}", dependencies=[Depends(require_manager_or_admin)])
async def delete_lead(lead_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> dict:
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="ליד לא נמצא")
    await db.delete(lead)
    await db.commit()
    return {"status": "deleted"}


@router.post("/{lead_id}/notes", response_model=NoteOut)
async def add_note(
    lead_id: uuid.UUID,
    payload: NoteCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Note:
    note = Note(lead_id=lead_id, user_id=current_user.id, body=payload.body)
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return note


@router.get("/{lead_id}/notes", response_model=list[NoteOut])
async def list_notes(lead_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> list[Note]:
    result = await db.execute(select(Note).where(Note.lead_id == lead_id).order_by(Note.created_at.desc()))
    return list(result.scalars().all())


@router.post("/{lead_id}/activities", response_model=ActivityOut)
async def add_activity(
    lead_id: uuid.UUID,
    payload: ActivityCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Activity:
    activity = Activity(
        lead_id=lead_id,
        user_id=current_user.id,
        activity_type=payload.activity_type,
        description=payload.description,
    )
    db.add(activity)
    await db.commit()
    await db.refresh(activity)
    return activity


@router.get("/{lead_id}/activities", response_model=list[ActivityOut])
async def list_activities(lead_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> list[Activity]:
    result = await db.execute(
        select(Activity).where(Activity.lead_id == lead_id).order_by(Activity.created_at.desc())
    )
    return list(result.scalars().all())


@router.post("/{lead_id}/ai-assistant")
async def ai_sales_assistant(
    lead_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Section 12: 'מה לעשות עכשיו?' - builds a strictly-factual summary of the lead
    from DB data only, then asks the AI engine to turn those facts into sales guidance."""
    result = await db.execute(
        select(Lead)
        .options(
            selectinload(Lead.lead_contacts).selectinload(LeadContact.contact),
            selectinload(Lead.tender),
            selectinload(Lead.project),
        )
        .where(Lead.id == lead_id)
    )
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="ליד לא נמצא")

    contacts = [lc.contact for lc in lead.lead_contacts if lc.contact]
    facts = {
        "title": lead.title,
        "record_type": lead.record_type.value,
        "domain": lead.domain.value if lead.domain else "לא נמצא",
        "city": lead.city or "לא נמצא",
        "estimated_value": str(lead.estimated_value) if lead.estimated_value else "לא נמצא",
        "deadline": lead.deadline.isoformat() if lead.deadline else "לא נמצא",
        "score": lead.score,
        "contacts": [
            {"name": c.name or "לא נמצא", "role": c.role or "לא נמצא", "phone": c.phone or "לא נמצא",
             "email": c.email or "לא נמצא"}
            for c in contacts
        ] or "לא נמצא איש קשר",
    }
    try:
        engine = AIEngine()
        advice = engine.generate_sales_assistant(json.dumps(facts, ensure_ascii=False))
    except AIUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    lead.ai_summary = advice.get("why_interesting")
    await db.commit()
    return advice
