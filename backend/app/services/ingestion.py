"""Turns a RawFinding (from a source adapter or search provider) into a persisted
Lead - the single choke point where dedup + scoring are applied consistently,
whether the trigger was a scheduled source scan, a manual search/run, or an import.
"""

import json
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import Confidence, LeadStatus, RecordType
from app.models.lead import Lead
from app.models.links import LeadSource
from app.services.adapters.base import RawFinding
from app.services.dedup import build_dedup_key, is_probable_duplicate
from app.services.scoring import ScoreInput, days_until, score_lead


def _safe_confidence(value: str) -> Confidence:
    try:
        return Confidence(value)
    except ValueError:
        return Confidence.MEDIUM


async def ingest_finding(
    db: AsyncSession,
    finding: RawFinding,
    *,
    source_id=None,
    source_name: str | None = None,
    record_type: RecordType = RecordType.TENDER,
    estimated_value: float | None = None,
    deadline: date | None = None,
    city: str | None = None,
    domain=None,
    has_contact_name: bool = False,
    has_phone: bool = False,
    has_email: bool = False,
    source_confidence: str = "medium",
) -> tuple[Lead, bool]:
    """Returns (lead, is_new). Applies dedup against existing leads with the same
    dedup_key; if found, updates last_verified_at/lead_sources instead of duplicating.
    """
    dedup_key = build_dedup_key(company_name=finding.title, city=city) or f"url:{finding.source_url}"

    existing_result = await db.execute(select(Lead).where(Lead.dedup_key == dedup_key))
    existing = existing_result.scalar_one_or_none()

    today = datetime.now(timezone.utc).date()
    score_input = ScoreInput(
        record_type=record_type,
        domain=domain,
        estimated_value=estimated_value,
        is_tender=record_type == RecordType.TENDER,
        tender_is_open=True,
        days_until_deadline=days_until(deadline, today),
        has_contact_name=has_contact_name,
        has_phone=has_phone,
        has_email=has_email,
        is_new_project=record_type == RecordType.PROJECT,
        is_early_stage=record_type == RecordType.PROJECT,
        source_confidence=source_confidence,
    )
    result = score_lead(score_input)

    if existing:
        existing.last_verified_at = datetime.now(timezone.utc)
        existing.score = result.total
        existing.tier = result.tier
        existing.score_breakdown_json = json.dumps(result.breakdown, ensure_ascii=False)
        db.add(
            LeadSource(
                lead_id=existing.id,
                source_id=source_id,
                source_url=finding.source_url,
                source_name=source_name,
                date_found=finding.found_at,
                last_checked=datetime.now(timezone.utc),
                still_exists=True,
                confidence=_safe_confidence(source_confidence),
            )
        )
        await db.flush()
        return existing, False

    lead = Lead(
        title=finding.title,
        record_type=record_type,
        domain=domain,
        city=city,
        estimated_value=estimated_value,
        deadline=deadline,
        score=result.total,
        tier=result.tier,
        score_breakdown_json=json.dumps(result.breakdown, ensure_ascii=False),
        status=LeadStatus.NEW,
        dedup_key=dedup_key,
        last_verified_at=datetime.now(timezone.utc),
    )
    db.add(lead)
    await db.flush()
    db.add(
        LeadSource(
            lead_id=lead.id,
            source_id=source_id,
            source_url=finding.source_url,
            source_name=source_name,
            date_found=finding.found_at,
            last_checked=datetime.now(timezone.utc),
            still_exists=True,
            confidence=Confidence.MEDIUM,
        )
    )
    await db.flush()
    return lead, True
