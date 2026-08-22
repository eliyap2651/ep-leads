import uuid
from datetime import date, datetime

from pydantic import BaseModel

from app.models.enums import (
    AlertChannel,
    AlertType,
    ScanFrequency,
    SourceStatus,
    SourceType,
    TaskStatus,
)


class SourceCreate(BaseModel):
    name: str
    url: str
    source_type: SourceType
    category: str | None = None
    scan_frequency: ScanFrequency = ScanFrequency.DAILY
    is_active: bool = True
    config_json: str | None = None
    notes: str | None = None


class SourceUpdate(BaseModel):
    name: str | None = None
    url: str | None = None
    source_type: SourceType | None = None
    category: str | None = None
    scan_frequency: ScanFrequency | None = None
    is_active: bool | None = None
    config_json: str | None = None
    notes: str | None = None


class SourceOut(BaseModel):
    id: uuid.UUID
    name: str
    url: str
    source_type: SourceType
    category: str | None
    scan_frequency: ScanFrequency
    is_active: bool
    status: SourceStatus
    last_scan_at: datetime | None
    last_success_at: datetime | None
    last_error: str | None
    result_count: int

    model_config = {"from_attributes": True}


class SearchQueryCreate(BaseModel):
    text: str
    category: str | None = None
    is_active: bool = True


class SearchQueryOut(BaseModel):
    id: uuid.UUID
    text: str
    category: str | None
    is_active: bool
    last_run_at: datetime | None
    result_count: int

    model_config = {"from_attributes": True}


class AlertOut(BaseModel):
    id: uuid.UUID
    lead_id: uuid.UUID | None
    alert_type: AlertType
    channel: AlertChannel
    title: str
    body: str | None
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TaskCreateSchema(BaseModel):
    lead_id: uuid.UUID | None = None
    title: str
    due_date: date | None = None
    assigned_to_id: uuid.UUID | None = None


class TaskOut(BaseModel):
    id: uuid.UUID
    lead_id: uuid.UUID | None
    title: str
    due_date: date | None
    status: TaskStatus
    assigned_to_id: uuid.UUID | None

    model_config = {"from_attributes": True}


class ContactOut(BaseModel):
    id: uuid.UUID
    name: str | None
    role: str | None
    phone: str | None
    whatsapp: str | None
    email: str | None
    source_url: str | None
    confidence: str

    model_config = {"from_attributes": True}


class SettingUpdate(BaseModel):
    key: str
    value: str | None
