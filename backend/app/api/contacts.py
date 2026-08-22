import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.database import get_db
from app.models.contact import Contact
from app.models.links import LeadContact
from app.schemas.misc import ContactOut

router = APIRouter(prefix="/contacts", tags=["contacts"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[ContactOut])
async def list_contacts(db: AsyncSession = Depends(get_db)) -> list[Contact]:
    result = await db.execute(select(Contact).order_by(Contact.created_at.desc()).limit(500))
    return list(result.scalars().all())


@router.get("/lead/{lead_id}", response_model=list[ContactOut])
async def contacts_for_lead(lead_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> list[Contact]:
    result = await db.execute(
        select(Contact).join(LeadContact, LeadContact.contact_id == Contact.id).where(LeadContact.lead_id == lead_id)
    )
    return list(result.scalars().all())
