"""Deterministic contact extraction (phones/emails) from raw text.

This is intentionally NOT AI-based: regex extraction of phone numbers and emails is
cheap, deterministic and far more reliable than an LLM for this narrow task (spec
section 40: "don't use AI for tasks that can be done deterministically and cheaply").
AI is used only afterwards to attach names/roles found nearby in context (see ai_engine.py).
"""

import re

import phonenumbers

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")

# Israeli phone patterns: 0X-XXXXXXX, 05X-XXXXXXX, +972-X-XXXXXXX, with/without dashes/spaces
PHONE_RE = re.compile(r"(?:\+972[-\s]?|0)(?:[23489]|5[0-9]|7[0-9])[-\s]?\d{3}[-\s]?\d{4}")


def extract_emails(text: str) -> list[str]:
    if not text:
        return []
    found = {m.group(0).lower() for m in EMAIL_RE.finditer(text)}
    # filter obvious non-business/placeholder addresses
    return sorted(e for e in found if not e.endswith((".png", ".jpg", ".gif")))


def extract_phones(text: str) -> list[str]:
    if not text:
        return []
    results = set()
    for m in PHONE_RE.finditer(text):
        raw = m.group(0)
        try:
            parsed = phonenumbers.parse(raw, "IL")
            if phonenumbers.is_valid_number(parsed):
                results.add(phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL))
        except phonenumbers.NumberParseException:
            continue
    return sorted(results)


def looks_like_business_whatsapp(phone_national: str) -> bool:
    """A mobile IL number (05X...) published alongside business contact info is a
    reasonable candidate for a business WhatsApp link. We never invent this - we only
    flag it as plausible so a human confirms before it is shown as a WhatsApp button."""
    digits = re.sub(r"\D", "", phone_national)
    return digits.startswith("05") and len(digits) == 10
