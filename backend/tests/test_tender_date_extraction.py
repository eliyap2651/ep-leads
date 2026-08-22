"""Deterministic date-related helpers used by the tender engine.

Full AI-based tender document extraction is covered by ai_engine.analyze_tender_document,
which requires a live ANTHROPIC_API_KEY and is intentionally NOT exercised in the default
test run (spec: never call paid external AI APIs from the standard test suite). Here we test
the deterministic pieces: days-until-deadline math, which drives urgency scoring and the
"closing soon" screens, and confirm the AI engine fails loudly (not silently) with no key.
"""

from datetime import date

import pytest

from app.services.ai_engine import AIEngine, AIUnavailableError
from app.services.scoring import days_until


def test_days_until_negative_for_past_dates():
    today = date(2026, 6, 1)
    assert days_until(date(2026, 5, 20), today) == -12


def test_ai_engine_raises_clear_error_without_api_key():
    engine = AIEngine(api_key=None)
    with pytest.raises(AIUnavailableError):
        engine.analyze_tender_document("some tender text")
