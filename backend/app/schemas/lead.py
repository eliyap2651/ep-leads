import uuid
from datetime import date, datetime

from pydantic import BaseModel

from app.models.enums import Domain, LeadStatus, LeadTier, RecordType, Region


class LeadListItem(BaseModel):
    id: uuid.UUID
    title: str
    record_type: RecordType
    domain: Domain | None
    city: str | None
    region: Region
    estimated_value: float | None
    deadline: date | None
    score: int
    tier: LeadTier
    status: LeadStatus
    created_at: datetime
    has_contact: bool = False
    has_phone: bool = False

    model_config = {"from_attributes": True}


class LeadUpdate(BaseModel):
    status: LeadStatus | None = None
    assigned_to_id: uuid.UUID | None = None
    title: str | None = None
    city: str | None = None
    region: Region | None = None
    estimated_value: float | None = None
    deadline: date | None = None


class LeadDetail(LeadListItem):
    address: str | None
    ai_summary: str | None
    score_breakdown_json: str | None
    company_id: uuid.UUID | None
    assigned_to_id: uuid.UUID | None
    is_stale: bool
    last_verified_at: datetime | None


class NoteCreate(BaseModel):
    body: str


class NoteOut(BaseModel):
    id: uuid.UUID
    body: str
    created_at: datetime
    user_id: uuid.UUID | None

    model_config = {"from_attributes": True}


class ActivityOut(BaseModel):
    id: uuid.UUID
    activity_type: str
    description: str | None
    created_at: datetime
    user_id: uuid.UUID | None

    model_config = {"from_attributes": True}


class ActivityCreate(BaseModel):
    activity_type: str
    description: str | None = None
