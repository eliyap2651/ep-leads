from app.models.enums import Domain, LeadTier, RecordType
from app.services.scoring import ScoreInput, days_until, score_lead
from datetime import date, timedelta


def test_hot_lead_scores_90_or_above():
    inp = ScoreInput(
        record_type=RecordType.TENDER, domain=Domain.HOTEL, estimated_value=1_500_000,
        is_tender=True, tender_is_open=True, days_until_deadline=2,
        has_contact_name=True, has_phone=True, has_email=True,
        is_direct_furniture_purchase=True, is_new_project=True,
        region_is_serviceable=True, source_confidence="high",
    )
    result = score_lead(inp)
    assert result.total >= 90
    assert result.tier == LeadTier.HOT


def test_low_lead_scores_under_55():
    inp = ScoreInput(record_type=RecordType.PROJECT, is_early_stage=True, source_confidence="low")
    result = score_lead(inp)
    assert result.total < 55
    assert result.tier == LeadTier.LOW


def test_score_never_exceeds_100():
    inp = ScoreInput(
        record_type=RecordType.TENDER, domain=Domain.MUNICIPALITY, estimated_value=10_000_000,
        is_tender=True, tender_is_open=True, days_until_deadline=1,
        has_contact_name=True, has_phone=True, has_email=True,
        is_direct_furniture_purchase=True, is_new_project=True, is_early_stage=True,
        region_is_serviceable=True, source_confidence="high",
    )
    result = score_lead(inp)
    assert result.total <= 100


def test_closed_tender_gets_no_urgency_points():
    inp = ScoreInput(record_type=RecordType.TENDER, is_tender=True, days_until_deadline=-5)
    result = score_lead(inp)
    assert result.breakdown["דחיפות (זמן עד מועד הגשה)"] == 0


def test_days_until_helper():
    today = date(2026, 1, 1)
    assert days_until(today + timedelta(days=10), today) == 10
    assert days_until(None, today) is None
