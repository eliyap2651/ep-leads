"""Deterministic Lead Scoring Engine (spec section 6).

The score (0-100) is computed from concrete, explainable factors only - no AI/LLM
involved, so it is fast, cheap, reproducible and auditable. Returns both the total
score and a breakdown so the UI/API can show "why" a lead got its score.
"""

from dataclasses import dataclass, field
from datetime import date

from app.models.enums import Domain, LeadTier, RecordType

# Domains considered a direct match for furniture-buying potential
DIRECT_FURNITURE_DOMAINS = {
    Domain.HOTEL,
    Domain.SCHOOL,
    Domain.KINDERGARTEN,
    Domain.YESHIVA,
    Domain.DORMITORY,
    Domain.NURSING_HOME,
    Domain.ASSISTED_LIVING,
    Domain.HOSPITAL,
    Domain.UNIVERSITY,
    Domain.OFFICE,
    Domain.HOSPITALITY,
}

GOV_LIKE_DOMAINS = {Domain.MUNICIPALITY, Domain.GOV_COMPANY, Domain.UNIVERSITY, Domain.HOSPITAL}


@dataclass
class ScoreInput:
    record_type: RecordType
    domain: Domain | None = None
    estimated_value: float | None = None
    unit_count: int | None = None  # rooms/units/beds - project size proxy
    is_tender: bool = False
    tender_is_open: bool = True
    days_until_deadline: int | None = None
    has_contact_name: bool = False
    has_phone: bool = False
    has_email: bool = False
    is_direct_furniture_purchase: bool = False
    is_new_project: bool = False
    is_early_stage: bool = False
    region_is_serviceable: bool = True
    source_confidence: str = "medium"  # high | medium | low


@dataclass
class ScoreResult:
    total: int
    tier: LeadTier
    breakdown: dict[str, int] = field(default_factory=dict)


def _clamp(value: int, low: int = 0, high: int = 100) -> int:
    return max(low, min(high, value))


def score_lead(inp: ScoreInput) -> ScoreResult:
    breakdown: dict[str, int] = {}

    # 1. Project size (0-18)
    size_points = 0
    if inp.estimated_value:
        if inp.estimated_value >= 1_000_000:
            size_points = 18
        elif inp.estimated_value >= 300_000:
            size_points = 14
        elif inp.estimated_value >= 100_000:
            size_points = 10
        elif inp.estimated_value >= 30_000:
            size_points = 5
        else:
            size_points = 2
    elif inp.unit_count:
        if inp.unit_count >= 150:
            size_points = 18
        elif inp.unit_count >= 60:
            size_points = 13
        elif inp.unit_count >= 20:
            size_points = 8
        else:
            size_points = 4
    breakdown["גודל פרויקט/כמות יחידות"] = size_points

    # 2. Body type (0-8)
    body_points = 8 if inp.domain in GOV_LIKE_DOMAINS else (5 if inp.domain else 0)
    breakdown["סוג הגוף"] = body_points

    # 3. Tender status (0-14)
    tender_points = 0
    if inp.is_tender:
        tender_points += 6
        if inp.tender_is_open:
            tender_points += 8
    breakdown["סטטוס מכרז (פתוח/קיים)"] = tender_points

    # 4. Time remaining to submit (0-10) - urgency without being too late
    urgency_points = 0
    if inp.days_until_deadline is not None:
        d = inp.days_until_deadline
        if d < 0:
            urgency_points = 0  # already closed
        elif d <= 3:
            urgency_points = 10
        elif d <= 10:
            urgency_points = 8
        elif d <= 21:
            urgency_points = 5
        else:
            urgency_points = 2
    breakdown["דחיפות (זמן עד מועד הגשה)"] = urgency_points

    # 5. Contact completeness (0-15)
    contact_points = 0
    if inp.has_contact_name:
        contact_points += 5
    if inp.has_phone:
        contact_points += 6
    if inp.has_email:
        contact_points += 4
    breakdown["שלמות פרטי קשר"] = contact_points

    # 6. Direct furniture relevance (0-15)
    relevance_points = 15 if inp.is_direct_furniture_purchase else (8 if inp.domain in DIRECT_FURNITURE_DOMAINS else 0)
    breakdown["התאמה למוצרי העסק (ריהוט ישיר)"] = relevance_points

    # 7. New project / early stage (0-10)
    stage_points = 0
    if inp.is_new_project:
        stage_points += 5
    if inp.is_early_stage:
        stage_points += 5
    breakdown["פרויקט חדש / שלב מוקדם"] = stage_points

    # 8. Region serviceable (0-5)
    region_points = 5 if inp.region_is_serviceable else 0
    breakdown["מיקום"] = region_points

    # 9. Source quality (0-5)
    source_points = {"high": 5, "medium": 3, "low": 1}.get(inp.source_confidence, 1)
    breakdown["איכות מקור המידע"] = source_points

    total = _clamp(sum(breakdown.values()))

    if total >= 90:
        tier = LeadTier.HOT
    elif total >= 75:
        tier = LeadTier.HIGH
    elif total >= 55:
        tier = LeadTier.MEDIUM
    else:
        tier = LeadTier.LOW

    return ScoreResult(total=total, tier=tier, breakdown=breakdown)


def days_until(target: date | None, today: date) -> int | None:
    if not target:
        return None
    return (target - today).days
