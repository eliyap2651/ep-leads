"""AI Engine - the only place in the codebase that calls an LLM (spec section 40).

Used strictly for tasks that genuinely need language understanding:
tender document analysis, project/opportunity classification, sales-assistant
message drafting, and summarizing "why this lead matters". Every prompt instructs
the model never to invent facts and to answer "לא נמצא" for anything not present
in the supplied source text - the model is a *reader*, not a source of facts.

Requires ANTHROPIC_API_KEY in the environment. If it's not set, callers receive a
clear AIUnavailableError instead of a silent fake response.
"""

import json
from dataclasses import dataclass

from anthropic import Anthropic, APIError

from app.config import get_settings

settings = get_settings()

TENDER_ANALYSIS_SYSTEM = """את/ה עוזר/ת ניתוח מכרזים למערכת EP LEADS.
קיבלת טקסט שחולץ ממסמך מכרז אמיתי. עליך לחלץ אך ורק מידע שמופיע במפורש בטקסט.
אסור בהחלט להמציא: מספרי טלפון, שמות אנשי קשר, תאריכים, סכומים, או כל פרט אחר.
אם פרט מסוים לא מופיע בטקסט - החזר בדיוק את המחרוזת "לא נמצא" עבור אותו שדה.
החזר תשובה כ-JSON תקני בלבד (ללא טקסט נוסף) במבנה הבא:
{
  "tender_title": "", "tender_number": "", "publishing_body": "", "field": "",
  "location": "", "publish_date": "", "submission_deadline": "", "site_visit_date": "",
  "contact_name": "", "contact_phone": "", "contact_email": "",
  "eligibility_conditions": "", "guarantees": "", "quantities": "",
  "furniture_items": "", "specifications": "", "installation_requirements": "",
  "delivery_requirements": "", "standards": "", "required_documents": "",
  "furniture_supplier_eligible": "לא נמצא", "classification_required": "",
  "estimated_value": "", "competition_level_estimate": "", "feasibility_notes": ""
}
תאריכים יש להחזיר בפורמט YYYY-MM-DD אם ידוע, אחרת "לא נמצא"."""

SALES_ASSISTANT_SYSTEM = """את/ה עוזר/ת מכירות בכיר/ה למערכת EP LEADS, המתמחה במכירת ריהוט
למוסדות, מלונות, פרויקטים ומכרזים בישראל. קיבלת סיכום עובדתי של ליד (רק עובדות שנאספו,
ללא המצאות). על סמך העובדות בלבד, כתוב תשובה מובנית ותכליתית בעברית עסקית.
אם עובדה חסרה (למשל אין שם איש קשר) - אמור זאת במפורש ואל תמציא שם.
החזר JSON תקני בלבד במבנה:
{
  "why_interesting": "", "who_to_contact": "", "what_to_ask": "",
  "what_to_offer": "", "how_to_open": "", "whatsapp_message": "",
  "email_draft": "", "call_script": "", "next_step": "", "follow_up_timing": ""
}"""


class AIUnavailableError(RuntimeError):
    pass


@dataclass
class AIEngine:
    api_key: str | None = None
    model: str | None = None

    def __post_init__(self) -> None:
        self.api_key = self.api_key or settings.ANTHROPIC_API_KEY
        self.model = self.model or settings.ANTHROPIC_MODEL
        self._client: Anthropic | None = None

    def _get_client(self) -> Anthropic:
        if not self.api_key:
            raise AIUnavailableError(
                "ANTHROPIC_API_KEY אינו מוגדר - הוסף אותו לקובץ .env כדי להפעיל את מנוע ה-AI"
            )
        if self._client is None:
            self._client = Anthropic(api_key=self.api_key)
        return self._client

    def _call(self, system: str, user_content: str, max_tokens: int = 2000) -> dict:
        client = self._get_client()
        try:
            response = client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user_content}],
            )
        except APIError as exc:  # network/auth/rate-limit errors from the API itself
            raise AIUnavailableError(f"שגיאת AI API: {exc}") from exc

        raw_text = "".join(block.text for block in response.content if block.type == "text").strip()
        try:
            return json.loads(raw_text)
        except json.JSONDecodeError:
            start, end = raw_text.find("{"), raw_text.rfind("}")
            if start != -1 and end != -1:
                return json.loads(raw_text[start : end + 1])
            raise

    def analyze_tender_document(self, document_text: str) -> dict:
        truncated = document_text[:120_000]  # keep within model context comfortably
        return self._call(TENDER_ANALYSIS_SYSTEM, truncated)

    def generate_sales_assistant(self, lead_fact_summary: str) -> dict:
        return self._call(SALES_ASSISTANT_SYSTEM, lead_fact_summary, max_tokens=1500)

    def classify_project_signal(self, raw_text: str) -> dict:
        system = """את/ה מסווג/ת טקסטים חדשותיים/עסקיים עבור EP LEADS כדי לזהות פרויקטים
מוקדמים (טרם מכרז) הרלוונטיים לרכש ריהוט (מלון חדש, בית ספר חדש, מפעל חדש וכו').
החזר JSON בלבד: {"is_relevant_project": true/false, "project_type": "", "confidence": "high/medium/low",
"reasoning": "", "extracted_entities": {"city": "לא נמצא", "developer": "לא נמצא", "unit_count": "לא נמצא"}}
אל תמציא נתונים שאינם בטקסט."""
        return self._call(system, raw_text[:40_000], max_tokens=800)
